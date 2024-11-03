"""Factory used in unit tests."""

import factory

from .models import User


class UserFactory(factory.django.DjangoModelFactory):
    """Creates mock users."""

    class Meta:
        """Meta options for UserFactory."""

        model = User

    handle = factory.Faker("word")
    display_name = factory.Faker("name")
    description = factory.Faker("text")
