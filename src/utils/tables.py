"""Django-tables2 shared stuff."""

from typing import TYPE_CHECKING

import django_tables2 as tables
from django.utils import timezone

if TYPE_CHECKING:
    from datetime import datetime


class LocalTimeColumn(tables.Column):
    """A table column which applies the active timezone."""

    def render(self, value: "datetime") -> "datetime":
        """Apply timezone to the value in the column."""
        return timezone.localtime(value)


class BPLocalTimeColumn(tables.Column):
    """A bp table column which applies the active timezone."""

    def __init__(self, *args, bp: str, **kwargs) -> None:  # type: ignore[no-untyped-def]  # noqa: ANN002,ANN003
        """Add breakpoint classes to attrs."""
        if "attrs" not in kwargs:
            kwargs["attrs"] = {}
        kwargs["attrs"].update(
            {
                "th": {"class": f"d-none d-{bp}-table-cell"},
                "td": {"class": f"d-none d-{bp}-table-cell"},
            }
        )
        super().__init__(*args, **kwargs)

    def render(self, value: "datetime") -> "datetime":
        """Apply timezone to the value in the column."""
        return timezone.localtime(value)


class BPColumn(tables.Column):
    """A column type that can be shown only on some breakpoints and up."""

    def __init__(self, *args, bp: str, **kwargs) -> None:  # type: ignore[no-untyped-def]  # noqa: ANN002,ANN003
        """Add breakpoint classes to attrs."""
        if "attrs" not in kwargs:
            kwargs["attrs"] = {}
        kwargs["attrs"].update(
            {
                "th": {"class": f"d-none d-{bp}-table-cell"},
                "td": {"class": f"d-none d-{bp}-table-cell"},
            }
        )
        super().__init__(*args, **kwargs)


class BPBooleanColumn(tables.BooleanColumn):
    """A BooleanColumn type that can be shown only on some breakpoints and up."""

    def __init__(self, *args, bp: str, **kwargs) -> None:  # type: ignore[no-untyped-def]  # noqa: ANN002,ANN003
        """Add breakpoint classes to attrs."""
        if "attrs" not in kwargs:
            kwargs["attrs"] = {}
        kwargs["attrs"].update(
            {
                "th": {"class": f"d-none d-{bp}-table-cell"},
                "td": {"class": f"d-none d-{bp}-table-cell"},
            }
        )
        super().__init__(*args, **kwargs)


class OverflowColumn(tables.Column):
    """A column type that permits text to break in any place."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]  # noqa: ANN002,ANN003
        """Add text-break class to <td>."""
        if "attrs" not in kwargs:
            kwargs["attrs"] = {}
        kwargs["attrs"].update(
            {
                "td": {"class": "text-break"},
            }
        )
        super().__init__(*args, **kwargs)


class BPOverflowColumn(tables.Column):
    """A breakpoint column type that permits text to break in any place."""

    def __init__(self, *args, bp: str, **kwargs) -> None:  # type: ignore[no-untyped-def]  # noqa: ANN002,ANN003
        """Add classes."""
        if "attrs" not in kwargs:
            kwargs["attrs"] = {}
        kwargs["attrs"].update(
            {
                "th": {"class": f"d-none d-{bp}-table-cell"},
                "td": {"class": f"d-none d-{bp}-table-cell text-break"},
            }
        )
        super().__init__(*args, **kwargs)
