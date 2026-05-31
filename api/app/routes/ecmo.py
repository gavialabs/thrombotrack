import datetime
import base64
import io
import os
from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    current_app as app,
    send_file,
    abort,
)
from PIL import Image
from uuid import UUID, uuid4
from sqlalchemy import func, delete
from sqlalchemy.orm import aliased
from werkzeug.utils import secure_filename
from .. import db
from ..models import Ecmo, Image as EcmoImage, AnnotationSession, Segmentation
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
from ..dto import AnnotateImagePayload
from ..helpers import decode_mask, encode_mask

# from .services import crop_diamond_oxygenator

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
GETINGE_ECMO_SIDE_LENGTH_MM = 88


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


ecmo_bp = Blueprint("ecmo", __name__, url_prefix="/ecmos")


@ecmo_bp.route("", methods=["GET"])
def get_ecmos():
    latest_annotated_image_time = (
        db.select(
            EcmoImage.ecmo_id, func.max(EcmoImage.created_at).label("max_created_at")
        )
        .where(EcmoImage.annotation_sessions.any(AnnotationSession.ended_at != None))
        .group_by(EcmoImage.ecmo_id)
        .subquery()
    )

    latest_annotated_image = aliased(EcmoImage)

    stmt = (
        db.select(
            Ecmo, latest_annotated_image.thumbnail, latest_annotated_image.clot_area, latest_annotated_image.fibrin_area
        )
        .outerjoin(
            latest_annotated_image_time,
            latest_annotated_image_time.c.ecmo_id == Ecmo.id,
        )
        .outerjoin(
            latest_annotated_image,
            (latest_annotated_image.ecmo_id == Ecmo.id)
            & (
                latest_annotated_image.created_at
                == latest_annotated_image_time.c.max_created_at
            ),
        )
        .order_by(func.lower(Ecmo.name))
    )
    results = db.session.execute(stmt)

    return EcmoSchema(many=True).dump(results)


@ecmo_bp.route("", methods=["POST"])
def create_ecmo():
    name = request.json.get("name")

    existing_ecmo = db.session.execute(
        db.select(Ecmo).filter_by(name=name)
    ).scalar_one_or_none()

    if existing_ecmo:
        return jsonify({}), 400

    ecmo = Ecmo(name=name)

    db.session.add(ecmo)
    db.session.commit()

    return (
        jsonify(
            {
                "id": ecmo.id,
                "name": name,
            }
        ),
        201,
    )


@ecmo_bp.route("/<uuid:ecmo_id>", methods=["PATCH"])
def edit_ecmo(ecmo_id: UUID):
    payload = EcmoSchema(partial=True).dump(request.json)

    ecmo = db.get_or_404(Ecmo, ecmo_id)

    name = payload.get("name")
    ecmo_type = payload.get("type")

    if name:
        ecmo.name = name
    if ecmo_type:
        ecmo.type = ecmo_type.upper()

    db.session.commit()

    return jsonify({}), 200


@ecmo_bp.route("/<uuid:ecmo_id>", methods=["DELETE"])
def delete_ecmo(ecmo_id: UUID):
    ecmo = db.get_or_404(Ecmo, ecmo_id)

    db.session.delete(ecmo)
    db.session.commit()

    return jsonify({}), 200


@ecmo_bp.route("/<uuid:ecmo_id>/images", methods=["POST"])
def upload_image(ecmo_id: UUID):
    ecmo = db.get_or_404(Ecmo, ecmo_id)

    if "image" not in request.files:
        return {"error": "No file part"}, 400

    image_file = request.files["image"]

    if image_file.filename == "":
        return {"error": "No selected file"}, 400

    if not allowed_file(image_file.filename):
        return {"error": "File type not allowed"}, 400

    ecmo_image = create_image(ecmo, image_file)

    return (
        jsonify(
            EcmoImageSchema(
                only=("id", "cropped", "mimetype", "current_annotation_session_id")
            ).dump(ecmo_image)
        ),
        200,
    )


@ecmo_bp.route(
    "/<uuid:ecmo_id>/images/<uuid:image_id>/annotation_sessions/<uuid:annotation_session_id>/segmentations",
    methods=["POST"],
)
def annotate_image(ecmo_id: UUID, image_id: UUID, annotation_session_id: UUID):
    payload: AnnotateImagePayload = SegmentationSchema(
        only=("path", "thrombus_type")
    ).load(request.json)

    ecmo = db.get_or_404(Ecmo, ecmo_id)
    image = db.get_or_404(EcmoImage, image_id)
    if image.ecmo_id != ecmo.id:
        abort(404)
    annotation_session = db.get_or_404(AnnotationSession, annotation_session_id)
    if annotation_session.image_id != image.id:
        abort(404)

    new_mask = create_segmentation(
        ecmo_image=image,
        annotation_session=annotation_session,
        path=payload["path"],
        annotation_type=payload["thrombus_type"],
    )

    # annotation_session has had its mask updated to include the latest segmentation
    return (
        jsonify(AnnotationSessionSchema(only=("mask",)).dump({"mask": new_mask})),
        201,
    )


@ecmo_bp.route(
    "/<uuid:ecmo_id>/images/<uuid:image_id>/annotation_sessions/<uuid:annotation_session_id>/undo",
    methods=["POST"],
)
def undo_last_segmentation(ecmo_id: UUID, image_id: UUID, annotation_session_id: UUID):
    ecmo = db.get_or_404(Ecmo, ecmo_id)
    image = db.get_or_404(EcmoImage, image_id)
    if image.ecmo_id != ecmo.id:
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
    "/<uuid:ecmo_id>/images/<uuid:image_id>/annotation_sessions/<uuid:annotation_session_id>/redo",
    methods=["POST"],
)
def redo_last_segmentation(ecmo_id: UUID, image_id: UUID, annotation_session_id: UUID):
    ecmo = db.get_or_404(Ecmo, ecmo_id)
    image = db.get_or_404(EcmoImage, image_id)
    if image.ecmo_id != ecmo.id:
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
    "/<uuid:ecmo_id>/images/<uuid:image_id>/annotation_sessions/<uuid:annotation_session_id>/end",
    methods=["POST"],
)
def end_annotation_session(ecmo_id: UUID, image_id: UUID, annotation_session_id: UUID):
    ecmo = db.get_or_404(Ecmo, ecmo_id)
    image = db.get_or_404(EcmoImage, image_id)
    if image.ecmo_id != ecmo.id:
        abort(404)
    annotation_session = db.get_or_404(AnnotationSession, annotation_session_id)
    if annotation_session.image_id != image.id:
        abort(404)

    annotation_session.ended_at = datetime.datetime.now()

    stmt = delete(Segmentation).where(
        Segmentation.annotation_session_id == annotation_session_id,
        Segmentation.undo == True,
    )
    db.session.execute(stmt)

    db.session.commit()

    return jsonify({}), 201


@ecmo_bp.route("/<uuid:ecmo_id>/history", methods=["GET"])
def get_history(ecmo_id: UUID):
    ecmo = db.get_or_404(Ecmo, ecmo_id)

    stmt = (
        db.select(
            EcmoImage.created_at,
            EcmoImage.clot_area,
            EcmoImage.fibrin_area,
        )
        .where(EcmoImage.ecmo_id == ecmo.id, EcmoImage.total_area != None)
        .order_by(EcmoImage.created_at)
    )
    result = db.session.execute(stmt).all()

    return (
        jsonify(
            EcmoImageSchema(
                many=True, only=("created_at", "clot_area", "fibrin_area", "total_area")
            ).dump(result)
        ),
        200,
    )


@ecmo_bp.route("/<uuid:ecmo_id>/gallery", methods=["GET"])
def get_gallery(ecmo_id: UUID):
    ecmo = db.get_or_404(Ecmo, ecmo_id)

    stmt = (
        db.select(
            EcmoImage.created_at,
            EcmoImage.thumbnail,
        )
        .where(EcmoImage.ecmo_id == ecmo.id)
        .order_by(EcmoImage.created_at)
    )
    result = db.session.execute(stmt).all()

    return (
        jsonify(
            EcmoImageSchema(many=True, only=("created_at", "thumbnail")).dump(result)
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
