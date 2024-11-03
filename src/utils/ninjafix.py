"""Workaround https://github.com/vitalik/django-ninja/issues/1266 for now."""

from typing import Any


def monkeypatch_ninja_uuid_converter() -> None:
    """Workaround https://github.com/vitalik/django-ninja/issues/1266 for now."""
    import importlib
    import sys

    import django.urls

    module_name = "ninja.signature.utils"
    sys.modules.pop(module_name, None)

    original_register_converter = django.urls.register_converter

    def fake_register_converter(*args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        pass

    django.urls.register_converter = fake_register_converter
    importlib.import_module(module_name)

    django.urls.register_converter = original_register_converter
