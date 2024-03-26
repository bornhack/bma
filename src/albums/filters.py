from ninja import Field
from typing import List
import uuid
from utils.filters import ListFilters

class AlbumFilters(ListFilters):
    """The filters used for the album_list endpoint."""

    files: List[uuid.UUID] = Field(None, alias="files")
