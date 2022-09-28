from ninja import ModelSchema

from audios.models import Audio


class AudioOutSchema(ModelSchema):
    class Config:
        model = Audio
        model_fields = "__all__"
