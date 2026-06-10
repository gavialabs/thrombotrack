import enum
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
]

TZDateTimeUpdated = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    ),
]


# Oxygenator -> Images -> Annotation Sessions -> Segmentations
# user is attached to an annotation session


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    object_id: Mapped[UUID]
    email: Mapped[str]
    name: Mapped[str]

    created_at: Mapped[TZDateTimeCreated]
    updated_at: Mapped[TZDateTimeUpdated]


class Oxygenator(db.Model):
    __tablename__ = "oxygenators"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(unique=True)
    type: Mapped[OxygenatorType] = mapped_column(
        Enum(OxygenatorType), default=OxygenatorType.HLS
    )

    created_at: Mapped[TZDateTimeCreated]
    updated_at: Mapped[TZDateTimeUpdated]

    images: Mapped[list["OxygenatorImage"]] = relationship(
        back_populates="oxygenator",
        cascade="all, delete",
        passive_deletes=True,
    )


class AnnotationSession(db.Model):
    __tablename__ = "annotation_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    image_id: Mapped[UUID] = mapped_column(
        ForeignKey("oxygenator_images.id", ondelete="CASCADE")
    )
    started_at: Mapped[TZDateTimeCreated]
    ended_at: Mapped[datetime | None]  # if this is non-null, we "saved" the annotations
    mask: Mapped[bytes] = mapped_column(LargeBinary)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    clot_area: Mapped[int] = mapped_column(default=0)  # annotated clot area (pixels)
    fibrin_area: Mapped[int] = mapped_column(
        default=0
    )  # annotated fibrin area (pixels)

    image: Mapped["OxygenatorImage"] = relationship(
        back_populates="annotation_sessions"
    )
    annotations: Mapped[list["Annotation"]] = relationship(
        back_populates="annotation_session",
        cascade="all, delete",
        passive_deletes=True,
    )


class OxygenatorImage(db.Model):
    __tablename__ = "oxygenator_images"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    oxygenator_id: Mapped[UUID] = mapped_column(ForeignKey("oxygenators.id", ondelete="CASCADE"))
    filename: Mapped[str]
    mimetype: Mapped[str]
    original: Mapped[bytes] = mapped_column(LargeBinary)
    thumbnail: Mapped[bytes] = mapped_column(LargeBinary)
    thumbnail_annotated: Mapped[bytes | None] = mapped_column(LargeBinary)
    cropped: Mapped[bytes] = mapped_column(LargeBinary)
    width_original: Mapped[int]
    height_original: Mapped[int]
    width_cropped: Mapped[int]
    height_cropped: Mapped[int]
    # define this column so that it can be used in subqueries below
    mm2_per_pixel: Mapped[float] = mapped_column(db.Float)
    created_at: Mapped[TZDateTimeCreated]

    current_annotation_session_id: Mapped[int | None] = column_property(
        select(AnnotationSession.id)
        .where(AnnotationSession.image_id == id)
        .order_by(AnnotationSession.started_at.desc())
        .limit(1)
        .correlate_except(AnnotationSession)
        .scalar_subquery()
    )

    clot_area: Mapped[float | None] = column_property(
        select(func.sum(AnnotationSession.clot_area) * mm2_per_pixel)
        .where(AnnotationSession.image_id == id, AnnotationSession.ended_at != None)
        .correlate_except(AnnotationSession)
        .scalar_subquery()
    )

    fibrin_area: Mapped[float | None] = column_property(
        select(func.sum(AnnotationSession.fibrin_area) * mm2_per_pixel)
        .where(AnnotationSession.image_id == id, AnnotationSession.ended_at != None)
        .correlate_except(AnnotationSession)
        .scalar_subquery()
    )

    oxygenator: Mapped["Oxygenator"] = relationship(back_populates="images")
    annotation_sessions: Mapped[list["AnnotationSession"]] = relationship(
        back_populates="image",
        cascade="all, delete",
        order_by="AnnotationSession.ended_at.desc()",
        passive_deletes=True,
    )


class Annotation(db.Model):
    __tablename__ = "annotations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    annotation_session_id: Mapped[UUID] = mapped_column(
        ForeignKey("annotation_sessions.id", ondelete="CASCADE")
    )
    type: Mapped[AnnotationType] = mapped_column(Enum(AnnotationType))
    path: Mapped[list[list[int]]] = mapped_column(JSONB)
    mask: Mapped[bytes] = mapped_column(LargeBinary)
    # explicitly separate clot/fibrin area since ERASE annotations can have both
    clot_area: Mapped[int]  # pixels
    fibrin_area: Mapped[int]
    undo: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[TZDateTimeCreated]

    annotation_session: Mapped["AnnotationSession"] = relationship(
        back_populates="annotations"
    )
