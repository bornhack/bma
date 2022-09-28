from ninja import ModelSchema

from pictures.models import Picture


class PictureOutSchema(ModelSchema):
    class Config:
        model = Picture
        model_fields = "__all__"
