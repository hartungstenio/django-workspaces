"""Django reusable app to manage user workspaces.

'Workspace' in this package is a unit of work. Each session always has one
active workspace. Anything can be added to a workspace.
"""

from typing import TYPE_CHECKING, Any, cast

import django_stubs_ext
from django.apps import apps as django_apps
from django.conf import settings
from django.http import Http404, HttpRequest
from django.shortcuts import aget_object_or_404, get_object_or_404

from .signals import workspace_requested
from .types import _Workspace, _WorkspaceModel

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser, AnonymousUser

django_stubs_ext.monkeypatch()

__all__ = [
    "aget_workspace",
    "get_workspace",
    "get_workspace_model",
    "workspace_requested",
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
    Workspace: _WorkspaceModel = get_workspace_model()  # noqa: N806
    user: AbstractUser | AnonymousUser = request.user

    try:
        workspace_id = Workspace._meta.pk.to_python(request.session[SESSION_KEY])  # noqa: SLF001
    except KeyError as exc:
        responses = workspace_requested.send(Workspace, user=user, request=request)
        if not responses:
            msg = "Could not find a workspace"
            raise Http404(msg) from exc

        _, workspace = cast("tuple[Any, _Workspace]", responses[0])
    else:
        workspace = get_object_or_404(Workspace, pk=workspace_id)

    return workspace


async def aget_workspace(request: HttpRequest) -> _Workspace:
    """Async version of :func:`get_workspace`."""
    Workspace: _WorkspaceModel = get_workspace_model()  # noqa: N806
    user: AbstractUser | AnonymousUser = await request.auser()

    session_workspace = await request.session.aget(SESSION_KEY)
    if session_workspace is None:
        responses = await workspace_requested.asend(Workspace, user=user, request=request)
        if not responses:
            msg = "Could not find a workspace"
            raise Http404(msg)

        _, workspace = cast("tuple[Any, _Workspace]", responses[0])
    else:
        workspace_id = Workspace._meta.pk.to_python(session_workspace)  # noqa: SLF001
        workspace = await aget_object_or_404(Workspace, pk=workspace_id)

    return workspace
