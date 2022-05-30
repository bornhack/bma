from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "public_credit_name", "description"]
    list_filter = ["username", "public_credit_name"]
