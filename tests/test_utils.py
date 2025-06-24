"""Tests for module functions."""

from unittest import mock

import pytest
from asgiref.sync import async_to_sync
from django.apps import apps
from django.contrib.auth.models import User
from django.http import Http404
from django.test.client import AsyncClient, AsyncRequestFactory, Client, RequestFactory
from pytest_django.fixtures import SettingsWrapper

from django_workspaces import SESSION_KEY, aget_workspace, get_workspace, get_workspace_model, workspace_requested
from django_workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def test_get_workspace_model_default(settings: SettingsWrapper) -> None:
    """Test if :func:'`get_workspace_model` defaults to :class:`Workspace`."""
    del settings.WORKSPACE_MODEL

    got = get_workspace_model()

    assert got is Workspace


def test_get_workspace_model_swapped(settings: SettingsWrapper) -> None:
    """Test if :func:'`get_workspace_model` gets the configured workspace model."""
    settings.INSTALLED_APPS += ["django.contrib.sites"]
    settings.WORKSPACE_MODEL = "sites.Site"

    got = get_workspace_model()

    assert got is apps.get_model("sites", "Site")


def test_get_workspace_with_session(settings: SettingsWrapper, rf: RequestFactory, client: Client) -> None:
    """Test if :func:`get_workspace` gets the session workspace."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    client.login(username="testuser", passworkd="testpw")
    expected: Workspace = Workspace.objects.create(name="test workspace")
    request = rf.get("/")
    request.user = user
    request.session = client.session
    request.session[SESSION_KEY] = str(expected.pk)

    got = get_workspace(request)

    assert got == expected


def test_get_workspace_with_session_non_existing(settings: SettingsWrapper, rf: RequestFactory, client: Client) -> None:
    """Test if :func:`get_workspace` raises exception when session workspace does not exist."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    client.login(username="testuser", passworkd="testpw")
    request = rf.get("/")
    request.user = user
    request.session = client.session
    request.session[SESSION_KEY] = "0"

    with pytest.raises(Http404):
        get_workspace(request)


def test_get_workspace_requests_signal(settings: SettingsWrapper, rf: RequestFactory, client: Client) -> None:
    """Test if :func:`get_workspace` uses requested workspace when there is no workspace in session."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    client.login(username="testuser", passworkd="testpw")
    expected: Workspace = Workspace.objects.create(name="test workspace")
    request = rf.get("/")
    request.user = user
    request.session = client.session
    mock_signal = mock.Mock(return_value=expected)

    workspace_requested.connect(mock_signal)
    try:
        got = get_workspace(request)

        assert got == expected
        mock_signal.assert_called_once_with(
            signal=workspace_requested,
            sender=Workspace,
            user=user,
            request=request,
        )
    finally:
        workspace_requested.disconnect(mock_signal)


def test_get_workspace_no_signal(settings: SettingsWrapper, rf: RequestFactory, client: Client) -> None:
    """Test if :func:`get_workspace` raises exception when there are no signals to respond workspace requests."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    client.login(username="testuser", passworkd="testpw")
    request = rf.get("/")
    request.user = user
    request.session = client.session

    with pytest.raises(Http404):
        get_workspace(request)


def test_get_workspace_requests_signal_none(settings: SettingsWrapper, rf: RequestFactory, client: Client) -> None:
    """Test if :func:`get_workspace` raises exception when signal return None."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    client.login(username="testuser", passworkd="testpw")
    request = rf.get("/")
    request.user = user
    request.session = client.session

    with pytest.raises(Http404):
        get_workspace(request)


def test_aget_workspace_with_session(
    settings: SettingsWrapper, async_rf: AsyncRequestFactory, async_client: AsyncClient
) -> None:
    """Test if :func:`aget_workspace` gets the session workspace."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    async_to_sync(async_client.alogin)(username="testuser", passworkd="testpw")
    expected: Workspace = Workspace.objects.create(name="test workspace")
    request = async_rf.get("/")

    async def auser() -> User:
        return user

    request.auser = auser
    request.session = async_client.session
    request.session[SESSION_KEY] = str(expected.pk)

    got = async_to_sync(aget_workspace)(request)

    assert got == expected


def test_aget_workspace_with_session_non_existing(
    settings: SettingsWrapper, async_rf: AsyncRequestFactory, async_client: AsyncClient
) -> None:
    """Test if :func:`aget_workspace` raises exception when session workspace does not exist."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    async_to_sync(async_client.alogin)(username="testuser", passworkd="testpw")
    request = async_rf.get("/")

    async def auser() -> User:
        return user

    request.auser = auser
    request.session = async_client.session
    request.session[SESSION_KEY] = "0"

    with pytest.raises(Http404):
        async_to_sync(aget_workspace)(request)


def test_aget_workspace_requests_signal(
    settings: SettingsWrapper, async_rf: AsyncRequestFactory, async_client: AsyncClient
) -> None:
    """Test if :func:`aget_workspace` uses requested workspace when there is no workspace in session."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    async_to_sync(async_client.alogin)(username="testuser", passworkd="testpw")
    expected: Workspace = Workspace.objects.create(name="test workspace")
    request = async_rf.get("/")

    async def auser() -> User:
        return user

    request.auser = auser
    request.session = async_client.session
    mock_signal = mock.AsyncMock(return_value=expected)

    workspace_requested.connect(mock_signal)
    try:
        got = async_to_sync(aget_workspace)(request)

        assert got == expected
        mock_signal.assert_awaited_once_with(
            signal=workspace_requested,
            sender=Workspace,
            user=user,
            request=request,
        )
    finally:
        workspace_requested.disconnect(mock_signal)


def test_aget_workspace_no_signal(
    settings: SettingsWrapper, async_rf: AsyncRequestFactory, async_client: AsyncClient
) -> None:
    """Test if :func:`aget_workspace` raises exception when there are no signals to respond workspace requests."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    async_to_sync(async_client.alogin)(username="testuser", passworkd="testpw")
    request = async_rf.get("/")

    async def auser() -> User:
        return user

    request.auser = auser
    request.session = async_client.session

    with pytest.raises(Http404):
        async_to_sync(aget_workspace)(request)


def test_aget_workspace_requests_signal_none(
    settings: SettingsWrapper, async_rf: AsyncRequestFactory, async_client: AsyncClient
) -> None:
    """Test if :func:`aget_workspace` raises exception when signal return None."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    async_to_sync(async_client.alogin)(username="testuser", passworkd="testpw")
    request = async_rf.get("/")

    async def auser() -> User:
        return user

    request.auser = auser
    request.session = async_client.session

    with pytest.raises(Http404):
        async_to_sync(aget_workspace)(request)
