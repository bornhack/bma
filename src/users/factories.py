import factory

from .models import User


class UserFactory(factory.django.DjangoModelFactory):
    """Creates mock users."""

    class Meta:
        """Meta options for UserFactory."""

        model = User

    public_credit_name = factory.Faker("name")
    description = factory.Faker("text")
