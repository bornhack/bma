from django.contrib.auth.mixins import UserPassesTestMixin


class OwnerOrAdminMixin(UserPassesTestMixin):
    """Only permit the object owner or an admin to use this view."""

    def test_func(self):
        if self.get_object().owner == self.request.user:
            return True
        if self.request.user.is_superuser:
            return True
