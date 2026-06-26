"""SQLAlchemy database model definitions.

The model hierarchy is Oxygenator -> Images -> Annotation Sessions -> Annotations. Users exist
separately and are associated with annotation sessions."""

from datetime import datetime
from sqlalchemy import (
    Enum,
    ForeignKey,
    func,
    select,
    DateTime,
    LargeBinary,
)
from sqlalchemy.orm import Mapped, mapped_column, column_property, relationship
from sqlalchemy.dialects.postgresql import JSONB
from typing import Annotated
from uuid import UUID, uuid4

from . import db
from .constants import OxygenatorType, AnnotationType

TZDateTimeCreated = Annotated[
    datetime, mapped_column(DateTime(timezone=True), server_default=func.now())
]  # helper type for a timezone-aware datetime field that defaults to now

TZDateTimeUpdated = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    ),
]  # same as above but updates with the new time whenever the row is edited


class Annotation(db.Model):
    """Output of a user's drawing on the image.

    Could be a segmentation of a clot or fibrin or an area that was erased. Stores the original
    coordinates of the user's path when drawing as well as a boolean mask of the annotation and
    how much clot or fibrin area it encompasses."""

    __tablename__ = "annotations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    annotation_session_id: Mapped[UUID] = mapped_column(
        ForeignKey("annotation_sessions.id", ondelete="CASCADE")
    )
    type: Mapped[AnnotationType] = mapped_column(Enum(AnnotationType))
    path: Mapped[list[list[int]]] = mapped_column(JSONB)
    mask: Mapped[bytes] = mapped_column(
        LargeBinary
    )  # boolean mask of the entire image area
    # explicitly separate clot/fibrin area since ERASE annotations can have both
    clot_area: Mapped[int]  # pixels
    fibrin_area: Mapped[int]
    undo: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[TZDateTimeCreated]

    annotation_session: Mapped["AnnotationSession"] = relationship(
        back_populates="annotations"
    )


class User(db.Model):
    """User logged in through Microsoft Entra."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    object_id: Mapped[UUID]  # unique ID from Microsoft Entra
    email: Mapped[str]
    name: Mapped[str]

    created_at: Mapped[TZDateTimeCreated]
    updated_at: Mapped[TZDateTimeUpdated]

    annotation_sessions: Mapped[list["AnnotationSession"]] = relationship(
        back_populates="user",
        cascade="all, delete",
        passive_deletes=True,
    )


class AnnotationSession(db.Model):
    """A session of annotations carried out by a single user.

    Sessions are started when an image is uploaded or viewed with &disabled=false. Multiple
    sessions can be associated with an image, with the latest being respected as the ground truth.
    """

    __tablename__ = "annotation_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    oxygenator_image_id: Mapped[UUID] = mapped_column(
        ForeignKey("oxygenator_images.id", ondelete="CASCADE")
    )
    started_at: Mapped[TZDateTimeCreated]
    ended_at: Mapped[datetime | None]  # if this is non-null, we "saved" the annotations
    mask: Mapped[bytes] = mapped_column(
        LargeBinary
    )  # boolean mask of the entire image area with all annotations overlaid
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    clot_area: Mapped[int] = mapped_column(default=0)  # annotated clot area (pixels)
    fibrin_area: Mapped[int] = mapped_column(
        default=0
    )  # annotated fibrin area (pixels)

    oxygenator_image: Mapped["OxygenatorImage"] = relationship(
        back_populates="annotation_sessions"
    )
    annotations: Mapped[list["Annotation"]] = relationship(
        back_populates="annotation_session",
        cascade="all, delete",
        passive_deletes=True,
    )
    user: Mapped["User"] = relationship(back_populates="annotation_sessions")


class OxygenatorImage(db.Model):
    """Image of an oxygenator, including the original and cropped versions."""

    __tablename__ = "oxygenator_images"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    oxygenator_id: Mapped[UUID] = mapped_column(
        ForeignKey("oxygenators.id", ondelete="CASCADE")
    )
    mimetype: Mapped[str]
    original: Mapped[bytes] = mapped_column(LargeBinary)
    thumbnail: Mapped[bytes] = mapped_column(LargeBinary)
    cropped: Mapped[bytes] = mapped_column(LargeBinary)
    thumbnail_annotated: Mapped[bytes | None] = mapped_column(LargeBinary)
    width_original: Mapped[int]
    height_original: Mapped[int]
    width_cropped: Mapped[int]
    height_cropped: Mapped[int]
    # define this column so that it can be used in subqueries below
    mm2_per_pixel: Mapped[float] = mapped_column(db.Float)

    created_at: Mapped[TZDateTimeCreated]

    last_annotation_session_id: Mapped[UUID | None] = column_property(
        select(AnnotationSession.id)
        .where(
            AnnotationSession.oxygenator_image_id == id,
            AnnotationSession.ended_at != None,
        )
        .order_by(AnnotationSession.ended_at.desc())
        .limit(1)
        .correlate_except(AnnotationSession)
        .scalar_subquery(),
        deferred=True,
    )

    oxygenator: Mapped["Oxygenator"] = relationship(back_populates="oxygenator_images")
    annotation_sessions: Mapped[list["AnnotationSession"]] = relationship(
        back_populates="oxygenator_image",
        cascade="all, delete",
        order_by="AnnotationSession.ended_at.desc()",
        passive_deletes=True,
    )


class Oxygenator(db.Model):
    """An oxygenator identified by a non-PII name and model type."""

    __tablename__ = "oxygenators"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(unique=True)
    type: Mapped[OxygenatorType] = mapped_column(
        Enum(OxygenatorType), default=OxygenatorType.HLS
    )

    created_at: Mapped[TZDateTimeCreated]
    updated_at: Mapped[TZDateTimeUpdated]

    last_annotated_oxygenator_image_id: Mapped[UUID | None] = column_property(
        select(OxygenatorImage.id)
        .where(
            OxygenatorImage.oxygenator_id == id,
            OxygenatorImage.thumbnail_annotated != None,
        )
        .order_by(OxygenatorImage.created_at.desc())
        .limit(1)
        .correlate_except(OxygenatorImage)
        .scalar_subquery(),
        deferred=True,
    )

    oxygenator_images: Mapped[list["OxygenatorImage"]] = relationship(
        back_populates="oxygenator",
        cascade="all, delete",
        passive_deletes=True,
    )
