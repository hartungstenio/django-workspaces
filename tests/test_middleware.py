"""Tests for workspace_middleware."""

import inspect
from unittest import mock

import pytest
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBase
from django.test.client import RequestFactory

from django_workspaces.middleware import _AsyncGetResponseCallable, _GetResponseCallable, workspace_middleware


@pytest.fixture
def get_response() -> _GetResponseCallable:
    """Return a dummy sync get_response function."""

    def middleware(request: HttpRequest, /) -> HttpResponse:
        return HttpResponse()

    return middleware


@pytest.fixture
def get_response_async() -> _AsyncGetResponseCallable:
    """Return a dummy async get_response function."""

    async def middleware(request: HttpRequest, /) -> HttpResponse:
        return HttpResponse()

    return middleware


def test_sync_middleware_chain(get_response: _GetResponseCallable, rf: RequestFactory, admin_user: User) -> None:
    """Test the sync middleware."""
    middleware: _GetResponseCallable = workspace_middleware(get_response)
    assert inspect.iscoroutinefunction(middleware) is False, "Expected a sync middleware. Got an async one"

    request = rf.get("/")
    with pytest.raises(ImproperlyConfigured):
        middleware(request)  # type: ignore[arg-type]
    assert not hasattr(request, "workspace"), "response should not have a workspace attribute"
    assert not hasattr(request, "aworkspace"), "response should not have an aworkspace attribute"

    request.user = admin_user

    expected_sync = mock.Mock()
    expected_async = mock.Mock()
    with (
        mock.patch("django_workspaces.middleware.get_workspace", return_value=expected_sync) as mock_get_workspace,
        mock.patch("django_workspaces.middleware.aget_workspace", return_value=expected_async) as mock_aget_workspace,
    ):
        got: HttpResponseBase = middleware(request)  # type: ignore[arg-type]

    assert isinstance(got, HttpResponseBase), f"Expected a response, got {type(got)}"

    assert hasattr(request, "workspace"), "response should have a workspace attribute"
    mock_get_workspace.assert_not_called()
    workspace = request.workspace
    assert workspace == expected_sync
    mock_get_workspace.assert_called_once()

    assert hasattr(request, "aworkspace"), "response should have an aworkspace attribute"
    mock_aget_workspace.assert_not_awaited()
    workspace = async_to_sync(request.aworkspace)()
    assert workspace == expected_async
    mock_aget_workspace.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_middleware_chain(
    get_response_async: _AsyncGetResponseCallable,
    rf: RequestFactory,
    admin_user: User,
) -> None:
    """Test the async middleware."""
    middleware: _AsyncGetResponseCallable = workspace_middleware(get_response_async)
    assert inspect.iscoroutinefunction(middleware), "Expected an async middleware. Got a sync one"

    request = rf.get("/")
    with pytest.raises(ImproperlyConfigured):
        await middleware(request)  # type: ignore[arg-type]
    assert not hasattr(request, "workspace"), "response should not have a workspace attribute"
    assert not hasattr(request, "aworkspace"), "response should not have an aworkspace attribute"

    async def aget_user() -> User:
        return admin_user

    request.auser = aget_user
    expected_sync = mock.Mock()
    expected_async = mock.Mock()
    with (
        mock.patch("django_workspaces.middleware.get_workspace", return_value=expected_sync) as mock_get_workspace,
        mock.patch("django_workspaces.middleware.aget_workspace", return_value=expected_async) as mock_aget_workspace,
    ):
        got: HttpResponseBase = await middleware(request)  # type: ignore[arg-type]

    assert isinstance(got, HttpResponseBase), f"Expected a response, got {type(got)}"

    assert hasattr(request, "workspace"), "response should have a workspace attribute"
    mock_get_workspace.assert_not_called()
    workspace = request.workspace
    assert workspace == expected_sync
    mock_get_workspace.assert_called_once()

    assert hasattr(request, "aworkspace"), "response should have an aworkspace attribute"
    mock_aget_workspace.assert_not_awaited()
    workspace = await request.aworkspace()
    assert workspace == expected_async
    mock_aget_workspace.assert_awaited_once()
