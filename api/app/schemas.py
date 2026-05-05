from . import ma
from .models import Ecmo

class EcmoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Ecmo