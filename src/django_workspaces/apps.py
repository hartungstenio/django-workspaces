"""Read by Django to configure :mod:`django_workspaces`."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WorkspacesConfig(AppConfig):
    """:mod:`django_workspaces` app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "django_workspaces"
    verbose_name = _("Workspaces")
