"""Django reusable app to manage user workspaces.

'Workspace' in this package is a unit of work. Each session always has one
active workspace. Anything can be added to a workspace.
"""

import django_stubs_ext
from django.apps import apps as django_apps
from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import aget_object_or_404, get_object_or_404

from .types import _Workspace, _WorkspaceModel

django_stubs_ext.monkeypatch()

__all__ = [
    "aget_workspace",
    "get_workspace",
    "get_workspace_model",
]

SESSION_KEY = "_workspace_id"


def get_workspace_model() -> _WorkspaceModel:
    """Return the workspace model that is active for this project.

    The workspace model defaults to :class:`django_workspaces.models.Workspace`, and can
    be swapped through the ``WORKSPACE_MODEL`` setting.
    """
    workspace_model_name: str = getattr(settings, "WORKSPACE_MODEL", "django_workspaces.Workspace")
    return django_apps.get_model(workspace_model_name, require_ready=False)


def get_workspace(request: HttpRequest) -> _Workspace:
    """Return the workspace model instance associated with the given request."""
    Workspace = get_workspace_model()  # noqa: N806
    workspace_id = Workspace._meta.pk.to_python(request.session[SESSION_KEY])  # noqa: SLF001
    # TODO(@hartungstenio): Get default workspace and save
    return get_object_or_404(Workspace, pk=workspace_id)


async def aget_workspace(request: HttpRequest) -> _Workspace:
    """Async version of :func:`get_workspace`."""
    Workspace = get_workspace_model()  # noqa: N806
    workspace_id = Workspace._meta.pk.to_python(await request.session.aget(SESSION_KEY))  # noqa: SLF001
    # TODO(@hartungstenio): Get default workspace and save
    return await aget_object_or_404(Workspace, pk=workspace_id)
