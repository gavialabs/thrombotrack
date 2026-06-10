import datetime
from flask import (
    Blueprint,
    Response,
    jsonify,
    request,
    abort,
)
from sqlalchemy import func, delete
from sqlalchemy.orm import aliased
from typing import Literal
from uuid import UUID

from .. import db
from ..dto import AnnotateImagePayload
from ..models import Oxygenator, OxygenatorImage, AnnotationSession, Annotation
from ..constants import ALLOWED_EXTENSIONS
from ..schemas import (
    EcmoSchema,
    EcmoImageSchema,
    SegmentationSchema,
    AnnotationSessionSchema,
    EcmoHistorySchema,
)
from ..services.ecmo import (
    create_image,
    create_segmentation,
    undo_segmentation,
    redo_segmentation,
)

ecmo_bp = Blueprint("oxygenators", __name__, url_prefix="/oxygenators")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@ecmo_bp.route("", methods=["GET"])
def get_oxygenators() -> tuple[Response, Literal[200]]:
    """Fetches a list of oxygenators.

    Gets the latest annotated image thumbnail to return with the oxygenator information.

    Returns:
        List of EcmoSchema with id, name, type, thumbnail, clot_area, and fibrin_area.
    """
    latest_annotated_image_time = (
        db.select(
            OxygenatorImage.oxygenator_id,
            func.max(OxygenatorImage.created_at).label("max_created_at"),
        )
        .where(OxygenatorImage.annotation_sessions.any(AnnotationSession.ended_at != None))
        .group_by(OxygenatorImage.oxygenator_id)
        .subquery()
    )

    latest_annotated_image = aliased(OxygenatorImage)

    stmt = (
        db.select(
            Oxygenator,
            latest_annotated_image.thumbnail,
            latest_annotated_image.clot_area,
            latest_annotated_image.fibrin_area,
        )
        .outerjoin(
            latest_annotated_image_time,
            latest_annotated_image_time.c.oxygenator_id == Oxygenator.id,
        )
        .outerjoin(
            latest_annotated_image,
            (latest_annotated_image.oxygenator_id == Oxygenator.id)
            & (
                latest_annotated_image.created_at
                == latest_annotated_image_time.c.max_created_at
            ),
        )
        .order_by(func.lower(Oxygenator.name))
    )
    results = db.session.execute(stmt)

    return (
        jsonify(
            EcmoSchema(
                many=True,
                only=("id", "name", "type", "thumbnail", "clot_area", "fibrin_area"),
            ).dump(results)
        ),
        200,
    )


@ecmo_bp.route("", methods=["POST"])
def create_oxygenator() -> tuple[Response, Literal[201]]:
    """Creates a new oxygenator in the database.

    Body:
        name: Unique name to identify the oxygenator.

    Returns:
        EcmoSchema with id, name, and type.
    """
    name = request.json.get("name")

    existing_ecmo = db.session.execute(
        db.select(Oxygenator).filter_by(name=name)
    ).scalar_one_or_none()

    if existing_ecmo:
        abort(400, description="name must be unique")

    ecmo = Oxygenator(name=name)

    db.session.add(ecmo)
    db.session.commit()

    return (
        jsonify(EcmoSchema(only=("id", "name", "type")).dump(ecmo)),
        201,
    )


@ecmo_bp.route("/<uuid:oxygenator_id>", methods=["PATCH"])
def edit_oxygenator(oxygenator_id: UUID) -> tuple[Response, Literal[200]]:
    """Changes name or type of an oxygenator.

    Args:
        oxygenator_id: ID of oxygenator object in database.

    Body:
        name: New name for oxygenator (optional).
        type: New type (HLS/Nautilus) for oxygenator (optional).
    """
    payload = EcmoSchema(only=("name", "type"), partial=True).dump(request.json)

    ecmo = db.get_or_404(Oxygenator, oxygenator_id)

    name = payload.get("name")
    ecmo_type = payload.get("type")

    if name:
        existing_ecmo = db.session.execute(
            db.select(Oxygenator).filter_by(name=name)
        ).scalar_one_or_none()

        if existing_ecmo:
            abort(400, description="name must be unique")

        ecmo.name = name

    if ecmo_type:
        ecmo.type = ecmo_type.upper()

    db.session.commit()

    return jsonify(), 200


@ecmo_bp.route("/<uuid:oxygenator_id>", methods=["DELETE"])
def delete_oxygenator(oxygenator_id: UUID) -> tuple[Response, Literal[200]]:
    """Deletes an oxygenator.

    Args:
        oxygenator_id: ID of oxygenator object in database.
    """
    ecmo = db.get_or_404(Oxygenator, oxygenator_id)

    db.session.delete(ecmo)
    db.session.commit()

    return jsonify(), 200


@ecmo_bp.route("/<uuid:oxygenator_id>/images", methods=["POST"])
def upload_image(oxygenator_id: UUID) -> tuple[Response, Literal[200]]:
    """Upload an image of an oxygenator.

    Args:
        oxygenator_id: ID of oxygenator in database.

    Form:
        image: Image of oxygenator.

    Returns:
        EcmoImageSchema with id, cropped, mimetype, and current_annotation_session_id.
    """
    oxygenator = db.get_or_404(Oxygenator, oxygenator_id)

    if "image" not in request.files:
        abort(400, description="No file part")

    image_file = request.files["image"]

    if image_file.filename == "":
        abort(400, description="No selected file")

    if not allowed_file(image_file.filename):
        abort(400, description="File type not allowed")

    oxygenator_image = create_image(oxygenator, image_file)

    return (
        jsonify(
            EcmoImageSchema(
                only=("id", "cropped", "mimetype", "current_annotation_session_id")
            ).dump(oxygenator_image)
        ),
        200,
    )


@ecmo_bp.route(
    "/<uuid:oxygenator_id>/images/<uuid:image_id>/annotation_sessions/<uuid:annotation_session_id>/segmentations",
    methods=["POST"],
)
def annotate_image(oxygenator_id: UUID, image_id: UUID, annotation_session_id: UUID):
    payload: AnnotateImagePayload = SegmentationSchema(
        only=("path", "thrombus_type")
    ).load(request.json)

    ecmo = db.get_or_404(Oxygenator, oxygenator_id)
    image = db.get_or_404(OxygenatorImage, image_id)
    if image.oxygenator_id != ecmo.id:
        abort(404)
    annotation_session = db.get_or_404(AnnotationSession, annotation_session_id)
    if annotation_session.image_id != image.id:
        abort(404)

    new_mask = create_segmentation(
        ecmo_image=image,
        annotation_session=annotation_session,
        path=payload["path"],
        annotation_type=payload["type"],
    )

    # annotation_session has had its mask updated to include the latest segmentation
    return (
        jsonify(AnnotationSessionSchema(only=("mask",)).dump({"mask": new_mask})),
        201,
    )


@ecmo_bp.route(
    "/<uuid:oxygenator_id>/images/<uuid:image_id>/annotation_sessions/<uuid:annotation_session_id>/undo",
    methods=["POST"],
)
def undo_last_segmentation(
    oxygenator_id: UUID, image_id: UUID, annotation_session_id: UUID
):
    ecmo = db.get_or_404(Oxygenator, oxygenator_id)
    image = db.get_or_404(OxygenatorImage, image_id)
    if image.oxygenator_id != ecmo.id:
        abort(404)
    annotation_session = db.get_or_404(AnnotationSession, annotation_session_id)
    if annotation_session.image_id != image.id:
        abort(404)

    new_mask = undo_segmentation(annotation_session)

    return (
        jsonify(AnnotationSessionSchema(only=("mask",)).dump({"mask": new_mask})),
        201,
    )


@ecmo_bp.route(
    "/<uuid:oxygenator_id>/images/<uuid:image_id>/annotation_sessions/<uuid:annotation_session_id>/redo",
    methods=["POST"],
)
def redo_last_segmentation(
    oxygenator_id: UUID, image_id: UUID, annotation_session_id: UUID
):
    ecmo = db.get_or_404(Oxygenator, oxygenator_id)
    image = db.get_or_404(OxygenatorImage, image_id)
    if image.oxygenator_id != ecmo.id:
        abort(404)
    annotation_session = db.get_or_404(AnnotationSession, annotation_session_id)
    if annotation_session.image_id != image.id:
        abort(404)

    new_mask = redo_segmentation(annotation_session)

    return (
        jsonify(AnnotationSessionSchema(only=("mask",)).dump({"mask": new_mask})),
        201,
    )


@ecmo_bp.route(
    "/<uuid:oxygenator_id>/images/<uuid:image_id>/annotation_sessions/<uuid:annotation_session_id>/end",
    methods=["POST"],
)
def end_annotation_session(
    oxygenator_id: UUID, image_id: UUID, annotation_session_id: UUID
):
    ecmo = db.get_or_404(Oxygenator, oxygenator_id)
    image = db.get_or_404(OxygenatorImage, image_id)
    if image.oxygenator_id != ecmo.id:
        abort(404)
    annotation_session = db.get_or_404(AnnotationSession, annotation_session_id)
    if annotation_session.image_id != image.id:
        abort(404)

    annotation_session.ended_at = datetime.datetime.now()

    stmt = delete(Annotation).where(
        Annotation.annotation_session_id == annotation_session_id,
        Annotation.undo == True,
    )
    db.session.execute(stmt)

    db.session.commit()

    return jsonify({}), 201


@ecmo_bp.route("/<uuid:oxygenator_id>/history", methods=["GET"])
def get_history(oxygenator_id: UUID):
    ecmo = db.get_or_404(Oxygenator, oxygenator_id)

    stmt = (
        db.select(
            OxygenatorImage.created_at.label("time"),
            (AnnotationSession.clot_area * OxygenatorImage.mm2_per_pixel).label("clot_area"),
            (AnnotationSession.fibrin_area * OxygenatorImage.mm2_per_pixel).label(
                "fibrin_area"
            ),
        )
        .join(OxygenatorImage, OxygenatorImage.id == AnnotationSession.image_id)
        .where(OxygenatorImage.oxygenator_id == ecmo.id)
        .order_by(OxygenatorImage.created_at)
    )
    result = db.session.execute(stmt).all()

    return (
        jsonify(EcmoHistorySchema(many=True).dump(result)),
        200,
    )


@ecmo_bp.route("/<uuid:oxygenator_id>/gallery", methods=["GET"])
def get_gallery(oxygenator_id: UUID):
    ecmo = db.get_or_404(Oxygenator, oxygenator_id)

    stmt = (
        db.select(
            OxygenatorImage.id,
            OxygenatorImage.created_at,
            func.coalesce(OxygenatorImage.thumbnail_annotated, OxygenatorImage.thumbnail).label(
                "thumbnail"
            ),
        )
        .where(OxygenatorImage.oxygenator_id == ecmo.id)
        .order_by(OxygenatorImage.created_at)
    )
    result = db.session.execute(stmt).all()

    return (
        jsonify(
            EcmoImageSchema(many=True, only=("id", "created_at", "thumbnail")).dump(
                result
            )
        ),
        200,
    )


@ecmo_bp.route("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.session.execute(db.text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return jsonify(
        {
            "status": "ok",
            "database": db_status,
            "message": "Flask PostgreSQL Template is running",
        }
    )
