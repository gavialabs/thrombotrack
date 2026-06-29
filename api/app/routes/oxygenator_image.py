"""Endpoints for interacting with oxygenator images.

/api/oxygenators/<id>/oxygenator_images:
    GET: Gets image history for an oxygenator.
    POST: Uploads an image of an oxygenator.
    GET /<id>: Gets an oxygenator image + latest annotated mask.
"""

from flask import Blueprint, Response, abort, jsonify, request, g
from typing import Literal
from uuid import UUID

from .. import db
from app.constants import ALLOWED_EXTENSIONS
from app.decorators import login_required
from app.models import AnnotationSession, Oxygenator, OxygenatorImage
from app.schemas import OxygenatorImageSchema
from app.services.annotation_session import (
    create_annotation_session,
)
from app.services.oxygenator_image import get_images, create_image

oxygenator_image_bp = Blueprint(
    # rooted at /api/oxygenators
    "oxygenator_images",
    __name__,
    url_prefix="/<uuid:oxygenator_id>/oxygenator_images",
)


@oxygenator_image_bp.route("", methods=["GET"])
@login_required
def get_gallery(oxygenator_id: UUID) -> tuple[Response, Literal[200]]:
    """Gets image history for an oxygenator.

    Args:
        oxygenator_id: ID of oxygenator to fetch image history for.

    Returns:
        List of OxygenatorImageSchema containing id, created_at, and thumbnail.
    """
    db.get_or_404(Oxygenator, oxygenator_id)

    result = get_images(oxygenator_id)

    return (
        jsonify(
            OxygenatorImageSchema(
                many=True, only=("id", "created_at", "thumbnail")
            ).dump(result)
        ),
        200,
    )


@oxygenator_image_bp.route("", methods=["POST"])
@login_required
def upload_image(oxygenator_id: UUID) -> tuple[Response, Literal[201]]:
    """Uploads an image of an oxygenator.

    Args:
        oxygenator_id: ID of oxygenator in database.

    Form:
        image: Image of oxygenator.

    Returns:
        OxygenatorImageSchema with id, cropped, mimetype, and current_annotation_session_id.
    """
    oxygenator = db.get_or_404(Oxygenator, oxygenator_id)

    if "image" not in request.files:
        abort(400, description="No file part")

    image_file = request.files["image"]

    if image_file.filename == "":
        abort(400, description="No selected file")

    if (
        "." not in image_file.filename
        or image_file.filename.rsplit(".", 1)[1].lower() not in ALLOWED_EXTENSIONS
    ):
        abort(400, description="File type not allowed")

    image_and_session = create_image(oxygenator, image_file)

    return (
        jsonify(
            OxygenatorImageSchema(
                only=("id", "cropped", "mimetype", "current_annotation_session_id")
            ).dump(image_and_session)
        ),
        201,
    )


@oxygenator_image_bp.route("/<uuid:oxygenator_image_id>", methods=["GET"])
@login_required
def view_image(
    oxygenator_id: UUID, oxygenator_image_id: UUID
) -> tuple[Response, Literal[200]]:
    """Gets an oxygenator image + latest annotated mask.

    This endpoint can be hit in three situations:
    1. Image has been annotated and the image is being viewed. In this case, we return the last
    annotation mask to display along with the image.
    2. Image has been annotated and a new annotation session is to be started. In this case, we
    copy the last annotation mask to a new session and return the new session ID with the image.
    3. Image has been annotated but the session was never ended. In this case, we return the
    in-progress annotation session ID along with the image.

    Args:
        oxygenator_id: ID of oxygenator to fetch image history for.
        oxygenator_image_id: ID of oxygenator image to fetch.

    Returns:
        OxygenatorImageSchema with id, cropped, mimetype, current_annotation_session_id, and mask.
    """
    oxygenator = db.get_or_404(Oxygenator, oxygenator_id)
    oxygenator_image = db.get_or_404(OxygenatorImage, oxygenator_image_id)
    if oxygenator_image.oxygenator_id != oxygenator.id:
        abort(404)

    # get the last unsaved annotation session ID to continue
    stmt = (
        db.select(AnnotationSession)
        .where(
            AnnotationSession.oxygenator_image_id == oxygenator_image_id,
            AnnotationSession.ended_at == None,
            AnnotationSession.user_id == g.get("user").id,
        )
        .order_by(AnnotationSession.started_at.desc())
    )
    current_annotation_session: AnnotationSession | None = db.session.execute(
        stmt
    ).scalar()

    payload = None
    if current_annotation_session is not None:
        # there's an ongoing annotation session, return it to finish
        payload = tuple(
            [
                oxygenator_image,
                current_annotation_session.id,
                current_annotation_session.mask,
            ]
        )
    elif oxygenator_image.last_annotation_session_id is not None:
        # image was previously annotated and session was ended
        last_annotation_session = db.get_or_404(
            AnnotationSession, oxygenator_image.last_annotation_session_id
        )

        if request.args.get("start_annotation_session") == "true":
            new_annotation_session = create_annotation_session(
                oxygenator_image, last_annotation_session, commit=True
            )
            payload = tuple(
                [
                    oxygenator_image,
                    new_annotation_session.id,
                    new_annotation_session.mask,
                ]
            )
        else:
            payload = tuple([oxygenator_image, None, last_annotation_session.mask])
    else:
        # the image was uploaded to the database but an annotation session was never started
        new_annotation_session = create_annotation_session(
            oxygenator_image, commit=True
        )
        payload = tuple(
            [
                oxygenator_image,
                new_annotation_session.id,
                new_annotation_session.mask,
            ]
        )

    return (
        jsonify(
            OxygenatorImageSchema(
                only=(
                    "id",
                    "cropped",
                    "mimetype",
                    "current_annotation_session_id",
                    "mask",
                )
            ).dump(payload)
        ),
        200,
    )
