"""Dummy processor for django-pictures."""


def dummy_processor(
    storage: tuple[str, list[str], dict[str, str]],
    file_name: str,
    new: list[tuple[str, list[str], dict[str, str]]] | None = None,
    old: list[tuple[str, list[str], dict[str, str]]] | None = None,
) -> None:
    """Dummy processor for django-pictures."""
