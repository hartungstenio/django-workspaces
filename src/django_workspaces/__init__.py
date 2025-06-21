"""Django reusable app to manage user workspaces.

'Workspace' in this package is a unit of work. Each session always has one
active workspace. Anything can be added to a workspace.
"""

import django_stubs_ext
from django.apps import apps as django_apps
from django.conf import settings
from django.http import HttpRequest

from .types import _Workspace, _WorkspaceModel

django_stubs_ext.monkeypatch()

__all__ = [
    "get_workspace_model",
]


def get_workspace_model() -> _WorkspaceModel:
    """Return the workspace model that is active for this project.

    The workspace model defaults to :class:`django_workspaces.models.Workspace`, and can
    be swapped through the ``WORKSPACE_MODEL`` setting.
    """
    workspace_model_name: str = getattr(settings, "WORKSPACE_MODEL", "django_workspaces.Workspace")
    return django_apps.get_model(workspace_model_name, require_ready=False)


def get_workspace(request: HttpRequest) -> _Workspace:
    """Return the workspace model instance associated with the given request."""
    raise NotImplementedError


async def aget_workspace(request: HttpRequest) -> _Workspace:
    """Async version of :func:`get_workspace`."""
    raise NotImplementedError
