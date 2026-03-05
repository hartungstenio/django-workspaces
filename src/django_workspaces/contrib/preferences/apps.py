"""Read by Django to configure :mod:`django_workspaces`."""

import asyncio
from typing import override

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from django_workspaces.signals import workspace_requested


class WorkspacePreferencesConfig(AppConfig):
    """:mod:`django_workspaces` app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "django_workspaces.contrib.preferences"
    verbose_name = _("Workspace Preferences")

    @override
    def ready(self) -> None:

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            from .signal_handlers import get_last_workspace  # noqa: PLC0415

            workspace_requested.connect(get_last_workspace)
        else:
            from .signal_handlers import aget_last_workspace  # noqa: PLC0415

            workspace_requested.connect(aget_last_workspace)
