"""Endpoints for interacting with annotation sessions.

/api/oxygenators/<id>/oxygenator_images/<id>/annotation_sessions/<id>:
    POST: Annotates an oxygenator image.
    POST /undo: Undoes the last annotation in a session.
    POST /redo: Redoes the last annotation in a session.
    POST /clear: Clears all annotations in a session.
    POST /end: Marks an annotation session as ended.
"""

from flask import Blueprint, Response, abort, jsonify, request
from typing import Literal
from uuid import UUID

from app import db
from app.decorators import login_required
from app.dto import AnnotateImagePayload
from app.models import AnnotationSession, Oxygenator, OxygenatorImage
from app.schemas import AnnotationSchema, AnnotationSessionSchema
from app.services.annotation_session import (
    create_annotation,
    end_annotation_session,
    redo_annotation,
    undo_annotation,
    clear_annotations,
)

annotation_session_bp = Blueprint(
    # rooted at /api/oxygenators/<id>/oxygenator_images
    "annotation_sessions",
    __name__,
    url_prefix="/<uuid:oxygenator_image_id>/annotation_sessions/<uuid:annotation_session_id>",
)


def access_check(
    oxygenator_id: UUID, oxygenator_image_id: UUID, annotation_session_id: UUID
) -> tuple[Oxygenator, OxygenatorImage, AnnotationSession]:
    """Checks if the oxygenator, oxygenator image, and annotation session exist and are linked."""
    oxygenator = db.get_or_404(Oxygenator, oxygenator_id)
    oxygenator_image = db.get_or_404(OxygenatorImage, oxygenator_image_id)
    if oxygenator_image.oxygenator_id != oxygenator.id:
        abort(404)
    annotation_session = db.get_or_404(AnnotationSession, annotation_session_id)
    if annotation_session.oxygenator_image_id != oxygenator_image.id:
        abort(404)

    return oxygenator, oxygenator_image, annotation_session


@annotation_session_bp.route(
    "",
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

    _, oxygenator_image, annotation_session = access_check(
        oxygenator_id, oxygenator_image_id, annotation_session_id
    )

    create_annotation(
        oxygenator_image=oxygenator_image,
        annotation_session=annotation_session,
        path=payload["path"],
        annotation_type=payload["type"],
    )

    return (
        jsonify(AnnotationSessionSchema(only=("mask",)).dump(annotation_session)),
        201,
    )


@annotation_session_bp.route(
    "/undo",
    methods=["POST"],
)
@login_required
def undo_last_annotation(
    oxygenator_id: UUID, oxygenator_image_id: UUID, annotation_session_id: UUID
) -> tuple[Response, Literal[201]]:
    """Undoes the last annotation in a session.

    Args:
        oxygenator_id: ID of oxygenator being annotated.
        oxygenator_image_id: ID of oxygenator image being annotated.
        annotation_session_id: ID of current annotation session.

    Returns:
        AnnotationSessionSchema with just the latest `mask`.
    """
    _, _, annotation_session = access_check(
        oxygenator_id, oxygenator_image_id, annotation_session_id
    )

    undo_annotation(annotation_session)

    return (
        jsonify(AnnotationSessionSchema(only=("mask",)).dump(annotation_session)),
        201,
    )


@annotation_session_bp.route(
    "/redo",
    methods=["POST"],
)
@login_required
def redo_last_annotation(
    oxygenator_id: UUID, oxygenator_image_id: UUID, annotation_session_id: UUID
) -> tuple[Response, Literal[201]]:
    """Redoes the last annotation in a session.

    Args:
        oxygenator_id: ID of oxygenator being annotated.
        oxygenator_image_id: ID of oxygenator image being annotated.
        annotation_session_id: ID of current annotation session.

    Returns:
        AnnotationSessionSchema with just the latest `mask`.
    """
    _, _, annotation_session = access_check(
        oxygenator_id, oxygenator_image_id, annotation_session_id
    )

    redo_annotation(annotation_session)

    return (
        jsonify(AnnotationSessionSchema(only=("mask",)).dump(annotation_session)),
        201,
    )


@annotation_session_bp.route(
    "/clear",
    methods=["POST"],
)
@login_required
def clear_all_annotations(
    oxygenator_id: UUID, oxygenator_image_id: UUID, annotation_session_id: UUID
) -> tuple[Response, Literal[201]]:
    """Clears all annotations in a session.

    Args:
        oxygenator_id: ID of oxygenator being annotated.
        oxygenator_image_id: ID of oxygenator image being annotated.
        annotation_session_id: ID of current annotation session.

    Returns:
        AnnotationSessionSchema with just the latest `mask`.
    """
    _, oxygenator_image, annotation_session = access_check(
        oxygenator_id, oxygenator_image_id, annotation_session_id
    )

    clear_annotations(annotation_session, oxygenator_image)

    return (
        jsonify(AnnotationSessionSchema(only=("mask",)).dump(annotation_session)),
        201,
    )


@annotation_session_bp.route(
    "/end",
    methods=["POST"],
)
@login_required
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
    _, _, annotation_session = access_check(
        oxygenator_id, oxygenator_image_id, annotation_session_id
    )

    end_annotation_session(annotation_session)

    return jsonify(), 200
