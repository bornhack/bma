"""Utilities for rendering image markup.

Originally borrowed from from https://github.com/codingjoe/django-pictures
"""

from __future__ import annotations

import math
import warnings
from fractions import Fraction
from typing import TYPE_CHECKING
from typing import TypeAlias

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = ["sizes", "get_widths"]

IntBreakpoints: TypeAlias = dict[str, int]
FloatBreakpoints: TypeAlias = dict[str, float]


class InvalidBreakpointError(KeyError):
    """Exception raised when an invalid breakpoint is used."""

    def __init__(self, bp: str, breakpoints: list[str]) -> None:
        super().__init__(f"Invalid breakpoint '{bp}' - available breakpoints: {breakpoints}")


def _grid(
    *,
    columns: int,
    settings: IntBreakpoints,
    **breakpoints: int,
) -> Iterator[tuple[str, float]]:
    """Calculate breakpoint percentage sizes from settings and the # of columns for each size.

    Example:
        # make the picture take up 12 columns on sm and md but only 9 columns on lg and up
        >>> for x in _grid(columns=12, settings={"sm": 600, "md": 900, "lg": 1200}, sm=12, lg=9):
        ...    print(x)
        ('sm', 1.0)
        ('md', 1.0)
        ('lg', 0.75)

    Args:
        columns (int): The total number of columns in the grid.
        settings (IntBreakpoints): A dict of supported breakpoints with the breakpoint
            name as key and the max width in pixels for that breakpoint.
        breakpoints (IntBreakpoints): The requested breakpoints and how many columns to take
            up at each size.

    Returns: A generator which yields a series of tuples of (breakpoint, percentage) where
             percentage is a number between 0 and 1.
    """
    # check for invalid breakpoints
    for key in breakpoints.keys() - settings.keys():
        raise InvalidBreakpointError(bp=key, breakpoints=list(settings.keys()))
    prev_size = columns
    # loop over breakpoint settings, yield size for each
    for bp in settings:
        prev_size = breakpoints.get(bp, prev_size)
        yield bp, prev_size / columns


def _media_query(
    *,
    container_width: int | None = None,
    settings: IntBreakpoints,
    **breakpoints: float,
) -> Iterator[str]:
    """Convert a set of breakpoint percentages to a CSS media query.

    Example:
        >>> for x in _media_query(settings={"sm": 600, "md": 900, "lg": 1200},
                sm=12, md=9, lg=6):
        ...     print(x)
        ...
        (min-width: 0px) and (max-width: 899px) 1200vw
        (min-width: 900px) and (max-width: 1199px) 900vw
        600vw

    Args:
        container_width (int): The max. width of the layout, optional. Leave at None if the
            layout has no max. width.
        settings (Breakpoints): The breakpoint settings for the layout.
        breakpoints (Breakpoints): The requested breakpoints and the percentage of the container
            a picture should take up at each breakpoint.

    Returns: A string containing a media query representing the provided breakpoints.
    """
    prev_ratio = None
    prev_width = 0
    for key, ratio in breakpoints.items():
        width = settings[key]
        if container_width and width >= container_width:
            yield f"(min-width: {prev_width}px) and (max-width: {container_width - 1}px) {math.floor(ratio * 100)}vw"
            break
        if prev_ratio and prev_ratio != ratio:
            yield f"(min-width: {prev_width}px) and (max-width: {width - 1}px) {math.floor(prev_ratio * 100)}vw"
            prev_width = width
        prev_ratio = ratio
    if prev_ratio:
        yield (
            f"{math.floor(prev_ratio * container_width)}px" if container_width else f"{math.floor(prev_ratio * 100)}vw"
        )
    else:
        warnings.warn("Your container is smaller than all your breakpoints.", UserWarning, stacklevel=2)
        yield f"{container_width}px" if container_width else "100vw"


def sizes(
    *,
    columns: int,
    settings: IntBreakpoints,
    container_width: int | None = None,
    **breakpoints: int,
) -> str:
    """Translate the requested breakpoints into a media query.

    First convert breakpoints from column counts to percentages of viewport width.
    Then convert the breakpoint percentages to a media query, optionally with a max container width.
    Return as a string which can be used in a media query directly.

    Examples:
        >>> kwargs=dict(columns=12, settings={"sm": 600, "md": 900, "lg": 1200}, sm=12, md=9, lg=6)
        >>> sizes(**kwargs)
        '(min-width: 0px) and (max-width: 899px) 100vw, (min-width: 900px) and (max-width: 1199px) 75vw, 50vw'
        >>> sizes(**kwargs, container_width=2000)
        '(min-width: 0px) and (max-width: 899px) 100vw, (min-width: 900px) and (max-width: 1199px) 75vw, 1000px'

    Args:
        columns (int): The number of columns in the layout
        settings (IntBreakpoints): The breakpoint settings for the layout.
        container_width (int): The max. width of the layout, optional. Leave at None if the
            layout has no max. width.
        breakpoints (IntBreakpoints): The requested breakpoints and the number of columns the
            picture should take up at each breakpoint.

    Returns: A mediaquery representing the requested breakpoints as a string
    """
    # get breakpoints as percentage
    float_bps = dict(
        _grid(
            columns=columns,
            settings=settings,
            **breakpoints,
        )
    )
    # return as media query
    return ", ".join(
        _media_query(
            container_width=container_width,
            settings=settings,
            **float_bps,
        )
    )


def get_widths(  # noqa: PLR0913
    *,
    original_size: tuple[int, int],
    ratio: str | Fraction | None,
    max_width: int,
    columns: int,
    pixel_densities: list[int],
    exclude_oversized: bool = True,
) -> set[int]:
    """Return required widths for a source picture size given ratio+max_width+columns+densities.

    Used to determine which sizes to generate when doing images and thumbnails.

    Args:
        original_size (tuple[int,int]): The dimensions of the parent image
        ratio (str|Fraction|None): Custom output ratio (optional)
        max_width (int): Maximum container width
        columns (int): The number of columns in the layout
        pixel_densities (list[int]): A list of pixel densities as integers
        exclude_oversized (bool): Set True to skip images larger than the original

    Returns: A set of integers with the needed sizes
    """
    img_width, img_height = original_size
    ratio = Fraction(ratio) if ratio else Fraction(img_width, img_height)
    # calc all column widths at 1X resolution
    widths = [max_width * (w + 1) / columns for w in range(columns)]
    # sizes for all pixel densities
    widths = [w * res for w in widths for res in pixel_densities]
    # exclude sizes above the original image width or height?
    if exclude_oversized:
        return {math.floor(w) for w in widths if w <= img_width and w / ratio <= img_height}
    return {math.floor(w) for w in widths}
