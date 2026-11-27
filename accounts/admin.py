
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    model = User

    list_display = (
        "phone_number",
        "name",
        "village",
        "district",
        "is_phone_verified",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "is_phone_verified",
        "is_staff",
        "is_active",
        "state",
    )

    search_fields = (
        "phone_number",
        "name",
        "village",
        "district",
    )

    ordering = ("phone_number",)

    fieldsets = (
        ("Authentication", {
            "fields": ("phone_number", "password")
        }),
        ("Personal Information", {
            "fields": (
                "name",
                "village",
                "district",
                "state",
                "pincode",
            )
        }),
        ("Verification", {
            "fields": ("is_phone_verified",)
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Important Dates", {
            "fields": ("last_login", "date_joined")
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "phone_number",
                "password1",
                "password2",
                "is_staff",
                "is_active",
            ),
        }),
    )
