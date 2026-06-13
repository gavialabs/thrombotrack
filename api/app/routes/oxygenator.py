from flask import (
    Blueprint,
    Response,
    jsonify,
    request,
    abort,
)
from typing import Literal
from uuid import UUID

from .. import db
from ..models import Oxygenator
from ..schemas import (
    OxygenatorSchema,
    AnnotationSessionSchema,
)
from ..services.oxygenator import (
    get_oxygenators,
    get_annotation_history,
)
from app.decorators import login_required

oxygenator_bp = Blueprint("oxygenators", __name__, url_prefix="/oxygenators")


@oxygenator_bp.route("", methods=["GET"])
@login_required
def get_oxygenator_list() -> tuple[Response, Literal[200]]:
    """Fetches a list of oxygenators.

    Gets the latest annotated image thumbnail to return with the oxygenator information.

    Returns:
        List of OxygenatorSchema with id, name, type, thumbnail, clot_area, fibrin_area, imaged_at, and
        annotated_by.
    """
    oxygenators = get_oxygenators()

    return (
        jsonify(
            OxygenatorSchema(
                many=True,
                only=(
                    "id",
                    "name",
                    "type",
                    "thumbnail",
                    "clot_area",
                    "fibrin_area",
                    "imaged_at",
                    "annotated_by",
                ),
            ).dump(oxygenators)
        ),
        200,
    )


@oxygenator_bp.route("", methods=["POST"])
@login_required
def create_oxygenator() -> tuple[Response, Literal[201]]:
    """Creates a new oxygenator in the database.

    Body:
        name: Unique name to identify the oxygenator.

    Returns:
        OxygenatorSchema with id, name, and type.
    """
    name = request.json.get("name")

    existing_oxygenator = db.session.execute(
        db.select(Oxygenator).filter_by(name=name)
    ).scalar_one_or_none()

    if existing_oxygenator:
        abort(400, description="name must be unique")

    oxygenator = Oxygenator(name=name)

    db.session.add(oxygenator)
    db.session.commit()

    return (
        jsonify(
            OxygenatorSchema(
                only=(
                    "id",
                    "name",
                    "type",
                    "thumbnail",
                    "clot_area",
                    "fibrin_area",
                    "imaged_at",
                    "annotated_by",
                )
            ).dump(oxygenator)
        ),
        201,
    )


@oxygenator_bp.route("/<uuid:oxygenator_id>", methods=["PATCH"])
@login_required
def edit_oxygenator(oxygenator_id: UUID) -> tuple[Response, Literal[200]]:
    """Changes name or type of an oxygenator.

    Args:
        oxygenator_id: ID of oxygenator object in database.

    Body:
        name: New name for oxygenator (optional).
        type: New type (HLS/Nautilus) for oxygenator (optional).
    """
    payload = OxygenatorSchema(only=("name", "type"), partial=True).dump(request.json)

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


@oxygenator_bp.route("/<uuid:oxygenator_id>", methods=["DELETE"])
@login_required
def delete_oxygenator(oxygenator_id: UUID) -> tuple[Response, Literal[200]]:
    """Deletes an oxygenator.

    Args:
        oxygenator_id: ID of oxygenator object in database.
    """
    ecmo = db.get_or_404(Oxygenator, oxygenator_id)

    db.session.delete(ecmo)
    db.session.commit()

    return jsonify(), 200


@oxygenator_bp.route("/<uuid:oxygenator_id>/history", methods=["GET"])
def get_history(oxygenator_id: UUID):
    """Gets a list of annotations for an oxygenator.

    Args:
        oxygenator_id: ID of oxygenator to fetch annotation history for.

    Returns:
        List of AnnotationSessionSchema containing ended_at, clot_area, and fibrin_area.
    """
    db.get_or_404(Oxygenator, oxygenator_id)

    history = get_annotation_history(oxygenator_id)

    return (
        jsonify(
            AnnotationSessionSchema(
                many=True, only=("imaged_at", "clot_area", "fibrin_area")
            ).dump(history)
        ),
        200,
    )
