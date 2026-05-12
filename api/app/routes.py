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
from sqlalchemy import func
from werkzeug.utils import secure_filename
from . import db
from .models import Ecmo, Image as EcmoImage, AnnotationSession
from .schemas import EcmoSchema, EcmoImageSchema, SegmentationSchema
from .services import create_image, create_segmentation

# from .services import crop_diamond_oxygenator

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
GETINGE_ECMO_SIDE_LENGTH_MM = 88


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


bp = Blueprint("main", __name__, url_prefix="/api")


@bp.route("/")
def index():
    """Home page with template information"""
    return render_template("index.html")


@bp.route("/ecmos")
def get_ecmos():
    ecmos = db.session.execute(
        db.select(Ecmo).order_by(func.lower(Ecmo.name))
    ).scalars()
    return EcmoSchema(many=True).dump(ecmos)


@bp.route("/ecmo", methods=["POST"])
def create_ecmo():
    name = request.json.get("name")

    existing_ecmo: Ecmo | None = db.session.execute(
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
                "name": name,
            }
        ),
        201,
    )


@bp.route("/ecmo/<uuid:ecmo_id>", methods=["PATCH"])
def edit_ecmo(ecmo_id: UUID):
    name = request.json.get("name")

    if not name:
        return jsonify({}), 400

    ecmo = db.get_or_404(Ecmo, ecmo_id)
    ecmo.name = name

    db.session.commit()

    return jsonify({}), 200


@bp.route("/ecmo/<uuid:ecmo_id>", methods=["DELETE"])
def delete_ecmo(ecmo_id: UUID):
    ecmo = db.get_or_404(Ecmo, ecmo_id)

    db.session.delete(ecmo)
    db.session.commit()

    return jsonify({}), 200


@bp.route("/ecmo/<uuid:ecmo_id>/images", methods=["POST"])
def upload_image(ecmo_id: UUID):
    ecmo = db.get_or_404(Ecmo, ecmo_id)

    # TODO - determine if this is a Getinge or Medtronic ECMO

    if "image" not in request.files:
        return {"error": "No file part"}, 400

    image_file = request.files["image"]

    if image_file.filename == "":
        return {"error": "No selected file"}, 400

    if not allowed_file(image_file.filename):
        return {"error": "File type not allowed"}, 400

    ecmo_image = create_image(ecmo_id, image_file)

    return (
        jsonify(
            EcmoImageSchema(
                only=("id", "cropped", "mimetype", "current_annotation_session_id")
            ).dump(ecmo_image)
        ),
        200,
    )


@bp.route(
    "/ecmo/<uuid:ecmo_id>/images/<uuid:image_id>/annotation_sessions/<uuid:annotation_session_id>/segmentations",
    methods=["POST"],
)
def annotate_image(ecmo_id: UUID, image_id: UUID, annotation_session_id: UUID):
    payload = SegmentationSchema(only=("x1", "y1", "x2", "y2")).load(request.json)

    ecmo = db.get_or_404(Ecmo, ecmo_id)
    image = db.get_or_404(EcmoImage, image_id)
    if image.ecmo_id != ecmo.id:
        abort(404)
    annotation_session = db.get_or_404(AnnotationSession, annotation_session_id)
    if annotation_session.image_id != image.id:
        abort(404)

    segmentation = create_segmentation(
        ecmo_image=image,
        annotation_session=annotation_session,
        x1=payload["x1"],
        y1=payload["y1"],
        x2=payload["x2"],
        y2=payload["y2"],
    )

    return jsonify(SegmentationSchema(only=("mask",)).dump(segmentation)), 201


@bp.route("/health")
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
