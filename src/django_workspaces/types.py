"""Type helpers."""

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, TypeAlias

from django.http import HttpRequest as DjangoHttpRequest

if TYPE_CHECKING:
    from .models import AbstractWorkspace

_Workspace: TypeAlias = "AbstractWorkspace"
"""Placeholder type for the current workspace.

The mypy plugin will refine it someday."""

_WorkspaceModel: TypeAlias = type[_Workspace]  # noqa: PYI047


class HttpRequest(DjangoHttpRequest):
    """HTTP request with workspace."""

    workspace: _Workspace
    aworkspace: Callable[[], Awaitable[_Workspace]]
