from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
from . import db


class Ecmo(db.Model):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class Image(db.Model):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    ecmo_id: Mapped[UUID] = mapped_column(ForeignKey("ecmo.id"))
    filename: Mapped[str]
    original_data: Mapped[bytes] = mapped_column(db.LargeBinary)
    cropped_data: Mapped[bytes] = mapped_column(db.LargeBinary)
    width_px: Mapped[int]
    height_px: Mapped[int]
    mm2_per_p2: Mapped[float]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class Annotation(db.Model):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    image_id: Mapped[UUID] = mapped_column(ForeignKey("image.id"))
    # contours: Mapped[list[list[list[int]]]]
    area_px: Mapped[float]
    created_at: Mapped[datetime]
