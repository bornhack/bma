from ninja import ModelSchema

from videos.models import Video


class VideoOutSchema(ModelSchema):
    class Config:
        model = Video
        model_fields = "__all__"
