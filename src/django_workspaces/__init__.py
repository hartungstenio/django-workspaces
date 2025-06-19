"""Django reusable app to manage user workspaces.

'Workspace' in this package is a unit of work. Each session always has one
active workspace. Anything can be added to a workspace.
"""

from typing import TYPE_CHECKING, TypeAlias

import django_stubs_ext
from django.apps import apps as django_apps
from django.conf import settings

if TYPE_CHECKING:
    from .models import AbstractWorkspace

django_stubs_ext.monkeypatch()

__all__ = [
    "get_workspace_model",
]

_Workspace: TypeAlias = "AbstractWorkspace"
"""Placeholder type for the current workspace.

The mypy plugin will refine it someday."""

_WorkspaceModel: TypeAlias = type[_Workspace]


def get_workspace_model() -> _WorkspaceModel:
    """Return the workspace model that is active for this project.

    The workspace model defaults to :class:`django_workspaces.models.Workspace`, and can
    be swapped through the ``WORKSPACE_MODEL`` setting.
    """
    workspace_model_name: str = getattr(settings, "WORKSPACE_MODEL", "django_workspaces.Workspace")
    return django_apps.get_model(workspace_model_name, require_ready=False)
