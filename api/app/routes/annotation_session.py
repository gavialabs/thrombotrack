from flask import Blueprint, Response, abort, jsonify, request
from typing import Literal
from uuid import UUID

from app import db
from app.decorators import login_required
from app.dto import AnnotateImagePayload
from app.models import AnnotationSession, Oxygenator, OxygenatorImage
from app.schemas import AnnotationSchema, AnnotationSessionSchema
from app.services.oxygenator import (
    create_annotation,
    end_annotation_session,
    redo_annotation,
    undo_annotation,
)

annotation_session_bp = Blueprint(
    # rooted at /api/oxygenators/<id>/oxygenator_images
    "annotation_sessions",
    __name__,
    url_prefix="/<uuid:oxygenator_image_id>/annotation_sessions",
)


@annotation_session_bp.route(
    "/<uuid:annotation_session_id>",
    methods=["POST"],
)
@login_required
def annotate_image(
    oxygenator_id: UUID, oxygenator_image_id: UUID, annotation_session_id: UUID
) -> tuple[Response, Literal[201]]:
    """Annotates an oxygenator image.

    Args:
        oxygenator_id: ID of oxygenator being annotated.
        oxygenator_image_id: ID of oxygenator image being annotated.
        annotation_session_id: ID of current annotation session.

    Returns:
        AnnotationSessionSchema with just the latest `mask`.
    """
    payload: AnnotateImagePayload = AnnotationSchema(only=("path", "type")).load(
        request.json
    )

    oxygenator = db.get_or_404(Oxygenator, oxygenator_id)
    oxygenator_image = db.get_or_404(OxygenatorImage, oxygenator_image_id)
    if oxygenator_image.oxygenator_id != oxygenator.id:
        abort(404)
    annotation_session = db.get_or_404(AnnotationSession, annotation_session_id)
    if annotation_session.oxygenator_image_id != oxygenator_image.id:
        abort(404)

    new_mask = create_annotation(
        oxygenator_image=oxygenator_image,
        annotation_session=annotation_session,
        path=payload["path"],
        annotation_type=payload["type"],
    )

    # annotation_session has had its mask updated to include the latest segmentation
    return (
        jsonify(AnnotationSessionSchema(only=("mask",)).dump({"mask": new_mask})),
        201,
    )


@annotation_session_bp.route(
    "/<uuid:annotation_session_id>/undo",
    methods=["POST"],
)
def undo_last_annotation(
    oxygenator_id: UUID, oxygenator_image_id: UUID, annotation_session_id: UUID
):
    oxygenator = db.get_or_404(Oxygenator, oxygenator_id)
    oxygenator_image = db.get_or_404(OxygenatorImage, oxygenator_image_id)
    if oxygenator_image.oxygenator_id != oxygenator.id:
        abort(404)
    annotation_session = db.get_or_404(AnnotationSession, annotation_session_id)
    if annotation_session.oxygenator_image_id != oxygenator_image.id:
        abort(404)

    new_mask = undo_annotation(annotation_session)

    return (
        jsonify(AnnotationSessionSchema(only=("mask",)).dump({"mask": new_mask})),
        201,
    )


@annotation_session_bp.route(
    "/<uuid:annotation_session_id>/redo",
    methods=["POST"],
)
def redo_last_annotation(
    oxygenator_id: UUID, oxygenator_image_id: UUID, annotation_session_id: UUID
):
    oxygenator = db.get_or_404(Oxygenator, oxygenator_id)
    oxygenator_image = db.get_or_404(OxygenatorImage, oxygenator_image_id)
    if oxygenator_image.oxygenator_id != oxygenator.id:
        abort(404)
    annotation_session = db.get_or_404(AnnotationSession, annotation_session_id)
    if annotation_session.oxygenator_image_id != oxygenator_image.id:
        abort(404)

    new_mask = redo_annotation(annotation_session)

    return (
        jsonify(AnnotationSessionSchema(only=("mask",)).dump({"mask": new_mask})),
        201,
    )


@annotation_session_bp.route(
    "/<uuid:annotation_session_id>/end",
    methods=["POST"],
)
def save_annotations(
    oxygenator_id: UUID, oxygenator_image_id: UUID, annotation_session_id: UUID
) -> tuple[Response, Literal[200]]:
    """Marks an annotation session as ended.

    Renders a new annotated thumbnail and deletes undone annotations from the database.

    Args:
        oxygenator_id: ID of oxygenator.
        oxygenator_image_id: ID of oxygenator image.
        annotation_session_id: ID of annotation session to end.

    Returns:
        Empty 200 response.
    """
    oxygenator = db.get_or_404(Oxygenator, oxygenator_id)
    oxygenator_image = db.get_or_404(OxygenatorImage, oxygenator_image_id)
    if oxygenator_image.oxygenator_id != oxygenator.id:
        abort(404)
    annotation_session = db.get_or_404(AnnotationSession, annotation_session_id)
    if annotation_session.oxygenator_image_id != oxygenator_image.id:
        abort(404)

    end_annotation_session(annotation_session)

    return jsonify(), 200
