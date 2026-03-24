"""Django reusable app to manage user workspaces.

'Workspace' in this package is a unit of work. Each session always has one
active workspace. Anything can be added to a workspace.
"""

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, cast, overload

import django_stubs_ext
from django.apps import apps as django_apps
from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest
from django.shortcuts import aget_object_or_404, get_object_or_404
from django.utils.translation import gettext as _

from .signals import workspace_entered, workspace_exited, workspace_requested
from .types import _Workspace, _WorkspaceModel

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser, AnonymousUser

django_stubs_ext.monkeypatch()

__all__ = [
    "aenter_workspace",
    "aget_workspace",
    "aget_workspace",
    "aleave_workspace",
    "aresolve_workspace",
    "aswitch_workspace",
    "enter_workspace",
    "get_workspace",
    "get_workspace",
    "get_workspace_model",
    "leave_workspace",
    "resolve_workspace",
    "switch_workspace",
    "workspace_entered",
    "workspace_exited",
    "workspace_requested",
]

SESSION_KEY = "_workspace_id"


def _resolve_user_session(
    obj: "AbstractUser | AnonymousUser | Mapping[str, Any] | HttpRequest",
    session: SessionBase | None = None,
) -> tuple["AbstractUser | AnonymousUser", SessionBase]:
    if isinstance(obj, HttpRequest):
        return obj.user, obj.session

    if isinstance(obj, Mapping):
        return obj["user"], obj["session"]

    if not session:
        msg = _("You must pass both a user and a session.")
        raise ValueError(msg)

    return cast("AbstractUser | AnonymousUser", obj), session


async def _aresolve_user_session(
    obj: "AbstractUser | AnonymousUser | Mapping[str, Any] | HttpRequest",
    session: SessionBase | None = None,
) -> tuple["AbstractUser | AnonymousUser", SessionBase]:
    if isinstance(obj, HttpRequest):
        return await obj.auser(), obj.session

    if isinstance(obj, Mapping):
        return obj["user"], obj["session"]

    if not session:
        msg = _("You must pass both a user and a session.")
        raise ValueError(msg)

    return cast("AbstractUser | AnonymousUser", obj), session


def _check_object_permission(user: "AbstractUser | AnonymousUser", workspace: _Workspace) -> None:
    if getattr(settings, "WORKSPACE_CHECK_OBJECT_PERMISSIONS", False):
        view_perm = f"{workspace._meta.app_label}.view_{workspace._meta.model_name}"
        if not user.has_perm(view_perm, workspace):
            raise PermissionDenied


async def _acheck_object_permission(user: "AbstractUser | AnonymousUser", workspace: _Workspace) -> None:
    if getattr(settings, "WORKSPACE_CHECK_OBJECT_PERMISSIONS", False):
        view_perm = f"{workspace._meta.app_label}.view_{workspace._meta.model_name}"
        has_perm = await user.ahas_perm(view_perm, workspace)
        if not has_perm:
            raise PermissionDenied


def get_workspace_model() -> _WorkspaceModel:
    """Return the workspace model that is active for this project.

    The workspace model defaults to :class:`django_workspaces.models.Workspace`, and can
    be swapped through the ``WORKSPACE_MODEL`` setting.
    """
    workspace_model_name: str = getattr(settings, "WORKSPACE_MODEL", "django_workspaces.Workspace")
    return django_apps.get_model(workspace_model_name, require_ready=False)


def resolve_workspace(user: "AbstractUser | AnonymousUser", session: SessionBase) -> _Workspace:
    """Resolve the current workspace for the given user.

    Args:
        user: the user in need of a workspace.
        session: the current session.
    Returns:
        The current workspace for the given user.
    Raises:
        :exc:`Http404`: if no workspace can be found.
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace resolved from the
            ``workspace_requested`` signal.
    """
    Workspace: _WorkspaceModel = get_workspace_model()  # noqa: N806

    try:
        workspace_id = Workspace._meta.pk.to_python(session[SESSION_KEY])
    except KeyError:
        responses = workspace_requested.send(Workspace, user=user)
        try:
            workspace = next(cast("_Workspace", value) for response in responses if (value := response[1]))
        except StopIteration as exc:
            msg = "Could not find a workspace"
            raise Http404(msg) from exc
        else:
            enter_workspace(user, workspace, session)
    else:
        workspace = get_object_or_404(Workspace, pk=workspace_id)

    return workspace


async def aresolve_workspace(user: "AbstractUser | AnonymousUser", session: SessionBase) -> _Workspace:
    """Resolve the current workspace for the given user.

    Async version of :func:`resolve_workspace`.

    Args:
        user: the user in need of a workspace.
        session: the current session.
    Returns:
        The current workspace for the given user.
    Raises:
        :exc:`Http404`: if no workspace can be found.
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace resolved from the
            ``workspace_requested`` signal.
    """
    Workspace: _WorkspaceModel = get_workspace_model()  # noqa: N806

    session_workspace = await session.aget(SESSION_KEY)
    if session_workspace is None:
        responses = await workspace_requested.asend(Workspace, user=user)
        try:
            workspace = next(cast("_Workspace", value) for response in responses if (value := response[1]))
        except StopIteration as exc:
            msg = "Could not find a workspace"
            raise Http404(msg) from exc
        else:
            await aenter_workspace(user, workspace, session)
    else:
        workspace_id = Workspace._meta.pk.to_python(session_workspace)
        workspace = await aget_object_or_404(Workspace, pk=workspace_id)

    return workspace


def get_workspace(request: HttpRequest) -> _Workspace:
    """Return the workspace model instance associated with the given request.

    Raises:
        :exc:`Http404`: if no workspace can be found.
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """
    if (workspace_header := getattr(settings, "WORKSPACE_ID_HEADER", None)) and (
        workspace_id := request.headers.get(workspace_header, None)
    ):
        return get_object_or_404(get_workspace_model(), pk=workspace_id)

    return resolve_workspace(request.user, request.session)


async def aget_workspace(request: HttpRequest) -> _Workspace:
    """Async version of :func:`get_workspace`.

    Raises:
        :exc:`Http404`: if no workspace can be found.
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """
    if (workspace_header := getattr(settings, "WORKSPACE_ID_HEADER", None)) and (
        workspace_id := request.headers.get(workspace_header, None)
    ):
        return await aget_object_or_404(get_workspace_model(), pk=workspace_id)

    user: AbstractUser | AnonymousUser = await request.auser()
    return await aresolve_workspace(user, request.session)


@overload
def enter_workspace(request: HttpRequest, /, workspace: _Workspace) -> None:
    """Change the current workspace for the user of the given request.

    Args:
        request: the authenticated request.
        workspace: the workspace being entered.
    Raises:
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """


@overload
def enter_workspace(scope: Mapping[str, Any], /, workspace: _Workspace) -> None:
    """Change the current workspace for the user of the given ASGI scope.

    Args:
        scope: the authenticated ASGI scope. Should have both user and session keys.
        workspace: the workspace being entered.
    Raises:
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """


@overload
def enter_workspace(user: "AbstractUser | AnonymousUser", /, workspace: _Workspace, session: SessionBase) -> None:
    """Change the current workspace for the given user.

    Args:
        user: the user entering the workspace.
        workspace: the workspace being entered.
        session: the current session.
    Raises:
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """


def enter_workspace(
    obj: "AbstractUser | AnonymousUser | Mapping[str, Any] | HttpRequest",
    workspace: _Workspace,
    session: SessionBase | None = None,
) -> None:
    """Change the current workspace for the given user.

    Args:
        user: the user entering the workspace.
        workspace: the workspace being entered.
        session: the current session.
    Raises:
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """
    user, session = _resolve_user_session(obj, session)
    _check_object_permission(user, workspace)
    session[SESSION_KEY] = workspace._meta.pk.value_to_string(workspace)
    workspace_entered.send(workspace.__class__, user=user, workspace=workspace)


@overload
async def aenter_workspace(request: HttpRequest, /, workspace: _Workspace) -> None:
    """Change the current workspace for the user of the given request.

    Async version of :func:`enter_workspace`.

    Args:
        request: the authenticated request.
        workspace: the workspace being entered.
    Raises:
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """


@overload
async def aenter_workspace(scope: Mapping[str, Any], /, workspace: _Workspace) -> None:
    """Change the current workspace for the user of the given ASGI scope.

    Async version of :func:`enter_workspace`.

    Args:
        scope: the authenticated ASGI scope. Should have both user and session keys.
        workspace: the workspace being entered.
    Raises:
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """


@overload
async def aenter_workspace(
    user: "AbstractUser | AnonymousUser",
    /,
    workspace: _Workspace,
    session: SessionBase,
) -> None:
    """Change the current workspace for the given user.

    Async version of :func:`enter_workspace`.

    Args:
        user: the user entering the workspace.
        workspace: the workspace being entered.
        session: the current session.
    Raises:
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """


async def aenter_workspace(
    obj: "AbstractUser | AnonymousUser | Mapping[str, Any] | HttpRequest",
    workspace: _Workspace,
    session: SessionBase | None = None,
) -> None:
    """Change the current workspace for the given user.

    Async version of :func:`enter_workspace`.

    Args:
        user: the user entering the workspace.
        workspace: the workspace being entered.
        session: the current session.
    Raises:
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """
    user, session = await _aresolve_user_session(obj, session)
    await _acheck_object_permission(user, workspace)
    await session.aset(SESSION_KEY, workspace._meta.pk.value_to_string(workspace))
    await workspace_entered.asend(workspace.__class__, user=user, workspace=workspace)


@overload
def leave_workspace(request: HttpRequest, /) -> None:
    """Make the user of the given request leave its current workspace.

    Args:
        request: the authenticated request.
    """


@overload
def leave_workspace(scope: Mapping[str, Any], /) -> None:
    """Make the user of the given ASGI scope leave its current workspace.

    Args:
        scope: the authenticated ASGI scope. Should have both user and session keys.
    """


@overload
def leave_workspace(user: "AbstractUser | AnonymousUser", /, session: SessionBase) -> None:
    """Make the user leave its current workspace.

    Args:
        user: the user leaving the workspace.
        session: the current session.
    """


def leave_workspace(
    obj: "AbstractUser | AnonymousUser | Mapping[str, Any] | HttpRequest",
    session: SessionBase | None = None,
) -> None:
    """Make the user leave its current workspace.

    Args:
        user: the user leaving the workspace.
        session: the current session.
    """
    user, session = _resolve_user_session(obj, session)
    if SESSION_KEY in session:
        workspace = resolve_workspace(user, session)
        del session[SESSION_KEY]
        workspace_exited.send(workspace.__class__, user=user, workspace=workspace)


@overload
async def aleave_workspace(request: HttpRequest, /) -> None:
    """Make the user of the given request leave its current workspace.

    Async version of :func:`leave_workspace`.

    Args:
        request: the authenticated request.
    """


@overload
async def aleave_workspace(scope: Mapping[str, Any], /) -> None:
    """Make the user of the given ASGI scope leave its current workspace.

    Async version of :func:`leave_workspace`.

    Args:
        scope: the authenticated ASGI scope. Should have both user and session keys.
    """


@overload
async def aleave_workspace(user: "AbstractUser | AnonymousUser", /, session: SessionBase) -> None:
    """Make the user leave its current workspace.

    Async version of :func:`leave_workspace`.

    Args:
        user: the user leaving the workspace.
        session: the current session.
    """


async def aleave_workspace(
    obj: "AbstractUser | AnonymousUser | Mapping[str, Any] | HttpRequest",
    session: SessionBase | None = None,
) -> None:
    """Make the user leave its current workspace.

    Async version of :func:`leave_workspace`.

    Args:
        user: the user leaving the workspace.
        session: the current session.
    """
    user, session = await _aresolve_user_session(obj, session)
    if await session.ahas_key(SESSION_KEY):
        workspace = await aresolve_workspace(user, session)
        await session.apop(SESSION_KEY)
        await workspace_exited.asend(workspace.__class__, user=user, workspace=workspace)


@overload
def switch_workspace(request: HttpRequest, /, workspace: _Workspace) -> None:
    """Switch the workspace for the user of the given request.

    Args:
        request: the authenticated request.
        workspace: the workspace being entered.
    Raises:
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """


@overload
def switch_workspace(scope: Mapping[str, Any], /, workspace: _Workspace) -> None:
    """Switch the workspace for the user of the given ASGI scope.

    Args:
        scope: the authenticated ASGI scope. Should have both user and session keys.
        workspace: the workspace being entered.
    Raises:
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """


@overload
def switch_workspace(user: "AbstractUser | AnonymousUser", /, workspace: _Workspace, session: SessionBase) -> None:
    """Switch the current user workspace.

    Args:
        user: the user entering the workspace.
        workspace: the workspace being entered.
        session: the current session.
    Raises:
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """


def switch_workspace(
    obj: "AbstractUser | AnonymousUser | Mapping[str, Any] | HttpRequest",
    workspace: _Workspace,
    session: SessionBase | None = None,
) -> None:
    """Switch the current user workspace.

    This is a shortcut to calling :func:`leave_workspace` and :func:`enter_workspace`

    Args:
        user: the user entering the workspace.
        workspace: the workspace being entered.
        session: the current session.
    Raises:
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """
    leave_workspace(obj, session)  # type: ignore[arg-type]
    enter_workspace(obj, workspace, session)  # type: ignore[arg-type]


@overload
async def aswitch_workspace(request: HttpRequest, /, workspace: _Workspace) -> None:
    """Switch the workspace for the user of the given request.

    Async version of :func:`switch_workspace`.

    Args:
        request: the authenticated request.
        workspace: the workspace being entered.
    Raises:
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """


@overload
async def aswitch_workspace(scope: Mapping[str, Any], /, workspace: _Workspace) -> None:
    """Switch the workspace for the user of the given ASGI scope.

    Async version of :func:`switch_workspace`.

    Args:
        scope: the authenticated ASGI scope. Should have both user and session keys.
        workspace: the workspace being entered.
    Raises:
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """


@overload
async def aswitch_workspace(
    user: "AbstractUser | AnonymousUser", /, workspace: _Workspace, session: SessionBase
) -> None:
    """Switch the current user workspace.

    Async version of :func:`switch_workspace`.

    Args:
        user: the user entering the workspace.
        workspace: the workspace being entered.
        session: the current session.
    Raises:
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """


async def aswitch_workspace(
    obj: "AbstractUser | AnonymousUser | Mapping[str, Any] | HttpRequest",
    workspace: _Workspace,
    session: SessionBase | None = None,
) -> None:
    """Switch the current user workspace.

    Async version of :func:`switch_workspace`.

    This is a shortcut to calling :func:`aleave_workspace` and :func:`aenter_workspace`

    Args:
        user: the user entering the workspace.
        workspace: the workspace being entered.
        session: the current session.
    Raises:
        :exc:`django.core.exceptions.PermissionDenied`: if permission validation is enabled
            and the user does not have view permission on the workspace.
    """
    await aleave_workspace(obj, session)  # type: ignore[arg-type]
    await aenter_workspace(obj, workspace, session)  # type: ignore[arg-type]
