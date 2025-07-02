"""Workspace middlewares."""

from collections.abc import Awaitable, Callable
from functools import partial
from typing import cast

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBase
from django.utils.decorators import sync_and_async_middleware
from django.utils.functional import SimpleLazyObject

from . import aget_workspace, get_workspace
from ._compat import iscoroutinefunction, markcoroutinefunction
from .types import HttpRequest, _Workspace

_Middleware = Callable[[HttpRequest], HttpResponseBase] | Callable[[HttpRequest], Awaitable[HttpResponseBase]]


@sync_and_async_middleware
def workspace_middleware(get_response: _Middleware, /) -> _Middleware:
    """Django middleware to add the current workspace to every request.

    Adds the property `workspace` to use in sync contexts, and the
    `aworkspace` corourine function for async contexts.
    """

    def middleware(request: HttpRequest) -> HttpResponseBase:
        if not hasattr(request, "user"):
            msg: str = "The workspace middleware requires Django's authentication middleware"
            raise ImproperlyConfigured(msg)

        request.workspace = cast("_Workspace", SimpleLazyObject(partial(get_workspace, request)))
        request.aworkspace = partial(aget_workspace, request)
        return get_response(request)  # type: ignore[return-value]

    if iscoroutinefunction(get_response):
        middleware = markcoroutinefunction(middleware)

    return middleware
