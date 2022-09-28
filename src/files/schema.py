from ninja import ModelSchema

from files.models import BaseFile
from utils.license import LicenseChoices


class UploadMetadata(ModelSchema):
    """The schema used for the upload API."""

    license: LicenseChoices

    class Config:
        model = BaseFile
        model_fields = ["license", "attribution"]
