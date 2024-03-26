from typing import Optional, List
from utils.filters import ListFilters, SortingChoices
from .models import FileTypeChoices
import uuid
from .models import LicenseChoices
from .models import StatusChoices

class FileFilters(ListFilters):
    """The filters used for the file_list endpoint."""

    sorting: SortingChoices = None
    albums: List[uuid.UUID] = None
    statuses: List[StatusChoices] = None
    owners: List[uuid.UUID] = None
    licenses: List[LicenseChoices] = None
    filetypes: List[FileTypeChoices] = None
    size: int = None
    size_lt: int = None
    size_gt: int = None
