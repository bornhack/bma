"""Custom taggit manager to include tagging user in lookup_kwargs, which is used to find through relations."""

from typing import TYPE_CHECKING
from typing import Any
from typing import Self

from django.contrib.postgres.aggregates import ArrayAgg
from django.db import models
from django.db.models import Count
from taggit.managers import _TaggableManager

from users.models import UserType

if TYPE_CHECKING:
    from .models import BmaTag


class BmaTagManager(_TaggableManager):
    """Custom taggit manager to include tagging user in lookup_kwargs, which is used to find through relations."""

    def get_queryset(self, *args: str) -> models.QuerySet["BmaTag"]:
        """Prefetch and annotate."""
        return (  # type: ignore[no-any-return]
            super()
            .get_queryset()
            .annotate(
                weight=models.Count("name"),
                tagger_uuids=ArrayAgg("taggings__tagger__pk"),
            )
            .order_by("-weight", "name", "created_at")
        )

    def _lookup_kwargs(self) -> dict[str, str | UserType]:
        """Override _lookup_kwargs to include the tagger/user in the lookup."""
        kwargs = self.through.lookup_kwargs(self.instance)
        kwargs["tagger"] = self.tagger
        return kwargs  # type: ignore[no-any-return]

    def add(self, *args: str, tagger: UserType, **kwargs: Any) -> None:  # noqa: ANN401
        """Make sure tagger is available for _lookup_kwargs when doing .add."""
        self.tagger = tagger
        super().add(*args, **kwargs)

    def set(self, *args: str, tagger: UserType, **kwargs: Any) -> None:  # noqa: ANN401
        """Make sure tagger is available for _lookup_kwargs when doing .set."""
        self.tagger = tagger
        super().set(*args, **kwargs)

    def remove(self, *args: str, tagger: UserType) -> None:
        """Make sure tagger is available for _lookup_kwargs when doing .remove."""
        self.tagger = tagger
        super().remove(*args)

    def clear(self, tagger: UserType) -> None:
        """Make sure tagger is available for _lookup_kwargs when doing .clear."""
        self.tagger = tagger
        super().clear()

    def similar_objects(self, tagger: UserType) -> models.QuerySet[Any]:
        """Make sure tagger is available for _lookup_kwargs when doing .similar_objects."""
        self.tagger = tagger
        return super().similar_objects()  # type: ignore[no-any-return]

    def add_user_tags(self, *tags: str, user: UserType) -> None:
        """Convenience method to add tag(s) for a user."""
        self.add(*tags, tagger=user, through_defaults={"tagger": user})


class BmaTagQuerySet(models.QuerySet):  # type: ignore[type-arg]
    """Custom queryset for tag operations."""

    def prefetch_hits(self) -> Self:
        """Prefetch hits for these tags."""
        return self.prefetch_related("hits")

    def prefetch_taggings_tagger(self) -> Self:
        """Prefetch taggings and taggers for these tags."""
        return self.prefetch_related("taggings__tagger")

    def annotate_hitcount(self) -> Self:
        """Annotate the hitcount for these tags."""
        return self.annotate(hitcount=Count("hits", distinct=True))

    def annotate_weight(self) -> Self:
        """Annotate the weight of these tags."""
        return self.annotate(weight=models.Count("name"))

    def annotate_tagger_uuids(self) -> Self:
        """Annotate the uuids of taggers for these tags."""
        return self.annotate(tagger_uuids=ArrayAgg("taggings__tagger__pk"))
