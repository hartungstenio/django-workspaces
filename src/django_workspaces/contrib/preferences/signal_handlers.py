from typing import Any

from django.contrib.auth.models import AbstractUser

from django_workspaces.models import AbstractWorkspace

from .models import WorkspacePreference


def get_last_workspace(
    sender: type[AbstractWorkspace],
    *,
    user: AbstractUser,
    **kwargs: Any,  # noqa: ANN401
) -> AbstractWorkspace | None:
    """Return the last workspace used by the user."""
    return WorkspacePreference.objects.select_related("last_workspace").filter(user=user).first()


async def aget_last_workspace(
    sender: type[AbstractWorkspace],
    *,
    user: AbstractUser,
    **kwargs: Any,  # noqa: ANN401
) -> AbstractWorkspace | None:
    """Return the last workspace used by the user.

    Async version of :func:`get_last_workspace`
    """
    return await WorkspacePreference.objects.select_related("last_workspace").filter(user=user).afirst()
