"""Model field and SimplePicture class for the pictures app.

Originally borrowed from from https://github.com/codingjoe/django-pictures
"""

from __future__ import annotations

import dataclasses
import math
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from django.conf import settings
from django.core import checks
from django.db.models import ImageField
from django.db.models.fields.files import ImageFieldFile

from pictures import utils

if TYPE_CHECKING:
    from collections.abc import Sequence

    from django.core.files.storage import Storage
    from django.db import models

__all__ = ["PictureField", "PictureFieldFile"]

RGB_FORMATS = ["JPEG"]


@dataclasses.dataclass
class SimplePicture:
    """A simple picture class similar to Django's image class."""

    parent_name: str
    file_type: str
    aspect_ratio: str | Fraction
    custom_aspect_ratio: bool
    storage: Storage
    width: int
    height: int

    def __post_init__(self) -> None:
        """Make sure ratio is a fraction."""
        if not isinstance(self.aspect_ratio, Fraction):
            self.aspect_ratio = Fraction(self.aspect_ratio)

    def __hash__(self) -> int:
        return hash(self.name)

    @property
    def url(self) -> str:
        return self.storage.url(self.name)

    @property
    def name(self) -> str:
        """Get the path under MEDIA_ROOT for this version of the image."""
        path = Path(self.parent_name).with_suffix("")
        if self.custom_aspect_ratio:
            path /= str(self.aspect_ratio).replace("/", "_")
        return str(path / f"{self.width}w.{self.file_type.lower()}")

    @property
    def path(self) -> Path:
        return Path(self.storage.path(self.name))

    def delete(self) -> None:
        self.storage.delete(self.name)


class PictureFieldFile(ImageFieldFile):
    """The picture edition of FieldFile."""

    field: PictureField  # help mypy a bit

    def get_picture_files(
        self,
        *,
        file_name: str,
        img_width: int,
        img_height: int,
        storage: Storage,
        exclude_oversized: bool = True,
    ) -> dict[Fraction | None, dict[str, dict[int, SimplePicture]]]:
        """Return a dict of ratio: filetype: width: SimplePicture nested dicts.

        Args:
            file_name (str): The filename of the source file
            img_width (int): The width of the source file
            img_height (int): The height of the source file
            storage (Storage): The storage class for the file
            exclude_oversized (bool): Return sizes smaller than the source

        Returns: A dict of ratio: filetype: width: SimplePicture nested dicts.
        """
        img_ratio = Fraction(img_width, img_height)
        return {
            ratio: {
                file_type: {
                    width: SimplePicture(
                        parent_name=file_name,
                        file_type=file_type,
                        aspect_ratio=ratio,
                        custom_aspect_ratio=custom,
                        storage=storage,
                        width=width,
                        height=math.floor(width / Fraction(ratio)) if ratio else math.floor(width / img_ratio),
                    )
                    for width in utils.get_widths(
                        original_size=(img_width, img_height),
                        ratio=ratio,
                        max_width=self.field.container_width,  # type: ignore[arg-type]
                        columns=self.field.grid_columns,  # type: ignore[arg-type]
                        pixel_densities=self.field.pixel_densities,  # type: ignore[arg-type]
                        exclude_oversized=exclude_oversized,
                    )
                }
                for file_type in self.field.file_types  # type: ignore[attr-defined]
            }
            for ratio, custom in [
                (Fraction(ratio), True) if ratio else (img_ratio, False)
                for ratio in self.field.aspect_ratios  # type: ignore[attr-defined]
            ]
        }

    @property
    def width(self) -> int:
        """Get width from the model field."""
        return self.instance.width  # type: ignore[no-any-return,attr-defined]

    @property
    def height(self) -> int:
        """Get height from the model field."""
        return self.instance.height  # type: ignore[no-any-return,attr-defined]

    def aspect_ratios(
        self, *, exclude_oversized: bool = True
    ) -> dict[Fraction | None, dict[str, dict[int, SimplePicture]]]:
        """Return a dict with ratio: filetype: width: SimplePicture nested dicts."""
        return self.get_picture_files(
            file_name=self.name,  # type: ignore[arg-type]
            img_width=self.width,
            img_height=self.height,
            storage=self.storage,
            exclude_oversized=exclude_oversized,
        )

    def get_picture_files_list(self, *, exclude_oversized: bool = True) -> set[SimplePicture]:
        """Return a list of SimplePicture objects."""
        return {
            picture
            for sources in self.aspect_ratios(exclude_oversized=exclude_oversized).values()
            for srcset in sources.values()
            for picture in srcset.values()
        }


class PictureField(ImageField):
    """The model field."""

    attr_class = PictureFieldFile

    def __init__(  # noqa: PLR0913
        self,
        verbose_name: str | None = None,
        name: str | None = None,
        aspect_ratios: list[str | Fraction | None] | None = None,
        container_width: int | None = None,
        file_types: list[str] | None = None,
        pixel_densities: list[int] | None = None,
        grid_columns: int | None = None,
        breakpoints: dict[str, int] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Use default settings if the field is missing some settings."""
        self.aspect_ratios = aspect_ratios or settings.PICTURES["ASPECT_RATIOS"]
        self.container_width = container_width or settings.PICTURES["CONTAINER_WIDTH"]
        self.file_types = file_types or settings.PICTURES["FILE_TYPES"]
        self.pixel_densities = pixel_densities or settings.PICTURES["PIXEL_DENSITIES"]
        self.grid_columns = grid_columns or settings.PICTURES["GRID_COLUMNS"]
        self.breakpoints = breakpoints or settings.PICTURES["BREAKPOINTS"]
        super().__init__(
            verbose_name=verbose_name,
            name=name,
            **kwargs,
        )

    def check(self, **kwargs: str) -> list[ValueError | checks.CheckMessage]:  # type: ignore[override]
        """Run the checks."""
        return super().check(**kwargs) + self._check_aspect_ratios() + self._check_width_height_field()  # type: ignore[operator]

    def _check_aspect_ratios(self) -> list[ValueError]:
        """Check each aspect ratio configured on the field."""
        errors = []
        if self.aspect_ratios:
            for ratio in self.aspect_ratios:  # type: ignore[attr-defined]
                if ratio is not None:
                    try:
                        Fraction(ratio)
                    except ValueError:
                        errors.append(
                            checks.Error(
                                "Invalid aspect ratio",
                                obj=self,
                                id="fields.E100",
                                hint="Aspect ratio must be a fraction, e.g. '16/9'",
                            )
                        )
        return errors  # type: ignore[return-value]

    def _check_width_height_field(self) -> list[checks.CheckMessage]:
        """Make sure width_field and height_field are present in the model."""
        if None in self.aspect_ratios and not (self.width_field and self.height_field):  # type: ignore[operator,attr-defined]
            return [
                checks.Warning(
                    "width_field and height_field attributes are missing",
                    obj=self,
                    id="fields.E101",
                    hint="Please add two positive integer fields to "
                    "'{self.model._meta.app_label}.{self.model.__name__}' and add their "
                    "field names as the 'width_field' and 'height_field' attribute for your "
                    "PictureField. Otherwise Django will not be able to cache the image "
                    "aspect size causing disk IO and potential response time increases.",
                )
            ]
        return []

    def deconstruct(self) -> tuple[str, str, Sequence[Any], dict[str, Any]]:
        """Return a tuple with the components needed to reconstruct the class."""
        name, path, args, kwargs = super().deconstruct()
        return (
            name,
            path,
            args,
            {
                **kwargs,
                "aspect_ratios": self.aspect_ratios,
                "container_width": self.container_width,
                "file_types": self.file_types,
                "pixel_densities": self.pixel_densities,
                "grid_columns": self.grid_columns,
                "breakpoints": self.breakpoints,
            },
        )

    def update_dimension_fields(self, instance: models.Model, force: bool = False, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401,FBT001,FBT002
        """Do nothing method to avoid Django ImageField reading the image dimensions using PIL."""
