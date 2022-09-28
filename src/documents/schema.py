from ninja import ModelSchema

from documents.models import Document


class DocumentOutSchema(ModelSchema):
    class Config:
        model = Document
        model_fields = "__all__"
