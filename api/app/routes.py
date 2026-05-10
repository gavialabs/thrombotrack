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
)
from PIL import Image
from uuid import UUID, uuid4
from sqlalchemy import func
from werkzeug.utils import secure_filename
from . import db
from .models import Ecmo, Image as EcmoImage
from .schemas import EcmoSchema

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


@bp.route("/ecmo/<uuid:ecmo_id>", methods=["POST"])
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

    filename = f"{uuid4().hex}_{secure_filename(image_file.filename)}"

    image_data = Image.open(image_file.stream)
    cropped = crop_diamond_oxygenator(image_data)

    square_pixels_area = cropped.shape[0] * cropped.shape[1]
    square_mm_area = GETINGE_ECMO_SIDE_LENGTH_MM**2
    mm2_per_p2 = square_mm_area / square_pixels_area

    image = EcmoImage(
        ecmo_id=ecmo_id,
        filename=filename,
        original_data=image_file.read(),
        cropped_data=cropped.tobytes(),
        width_px=image_data.width,
        height_px=image_data.height,
        mm2_per_p2=mm2_per_p2,
    )
    db.session.add(image)
    db.session.commit()

    image_data.close()
    image_file.close()

    img = Image.fromarray(cropped)
    file_object = io.BytesIO()
    img.save(file_object, "jpeg")
    file_object.seek(0)

    return jsonify(
        {
            "image_id": image.id,
            "image": base64.b64encode(file_object.read()).decode("utf-8"),
            "mime_type": "image/jpeg",  # TODO - support any image mime type uploaded
        }
    )


@bp.route("/ecmo/<uuid:ecmo_id>/images/<uuid:image_id>/segmentations", methods=["POST"])
def create_segmentation(ecmo_id: UUID, image_id: UUID):
    # /payload = AnnotationSchema().load(request.json)
    pass


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
