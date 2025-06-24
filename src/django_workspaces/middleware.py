"""Workspace middlewares."""

import inspect
from collections.abc import Awaitable
from functools import partial
from typing import Protocol, cast, overload

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBase
from django.utils.decorators import sync_and_async_middleware
from django.utils.functional import SimpleLazyObject

from . import aget_workspace, get_workspace
from ._compat import TypeIs
from .types import HttpRequest, _Workspace


class _GetResponseCallable(Protocol):
    def __call__(self, request: HttpRequest, /) -> HttpResponseBase: ...


class _AsyncGetResponseCallable(Protocol):
    def __call__(self, request: HttpRequest, /) -> Awaitable[HttpResponseBase]: ...


def _is_async_middleware(arg: _GetResponseCallable | _AsyncGetResponseCallable) -> TypeIs[_AsyncGetResponseCallable]:
    return inspect.iscoroutinefunction(arg)


@overload
def workspace_middleware(get_response: _GetResponseCallable, /) -> _GetResponseCallable:
    pass


@overload
def workspace_middleware(get_response: _AsyncGetResponseCallable, /) -> _AsyncGetResponseCallable:
    pass


@sync_and_async_middleware
def workspace_middleware(
    get_response: _GetResponseCallable | _AsyncGetResponseCallable, /
) -> _GetResponseCallable | _AsyncGetResponseCallable:
    """Django middleware to add the current workspace to every request.

    Adds the property `workspace` to use in sync contexts, and the
    `aworkspace` corourine function for async contexts.
    """
    middleware: _GetResponseCallable | _AsyncGetResponseCallable

    if not _is_async_middleware(get_response):

        def middleware(request: HttpRequest) -> HttpResponseBase:
            if not hasattr(request, "user"):
                msg: str = "The workspace middleware requires Django's authentication middleware"
                raise ImproperlyConfigured(msg)

            request.workspace = cast("_Workspace", SimpleLazyObject(partial(get_workspace, request)))
            request.aworkspace = partial(aget_workspace, request)
            return get_response(request)
    else:

        async def middleware(request: HttpRequest) -> HttpResponseBase:
            if not hasattr(request, "auser"):
                msg: str = "The workspace middleware requires Django's authentication middleware"
                raise ImproperlyConfigured(msg)

            request.workspace = cast("_Workspace", SimpleLazyObject(partial(get_workspace, request)))
            request.aworkspace = partial(aget_workspace, request)
            return await get_response(request)

    return middleware
