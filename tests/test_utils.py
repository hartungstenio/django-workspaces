"""Tests for module functions."""

from unittest import mock

import pytest
from asgiref.sync import async_to_sync
from django.apps import apps
from django.contrib.auth.models import User
from django.http import Http404
from django.test.client import AsyncClient, AsyncRequestFactory, Client, RequestFactory
from pytest_django.fixtures import SettingsWrapper

from django_workspaces import (
    SESSION_KEY,
    aenter_workspace,
    aget_workspace,
    aleave_workspace,
    aswitch_workspace,
    enter_workspace,
    get_workspace,
    get_workspace_model,
    leave_workspace,
    switch_workspace,
    workspace_entered,
    workspace_exited,
    workspace_requested,
)
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
        with mock.patch("django_workspaces.enter_workspace") as mock_enter:
            got = get_workspace(request)

        assert got == expected
        mock_enter.assert_called_once_with(user, got, request.session)
        mock_signal.assert_called_once_with(
            signal=workspace_requested,
            sender=Workspace,
            user=user,
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
        with mock.patch("django_workspaces.aenter_workspace") as mock_aenter:
            got = async_to_sync(aget_workspace)(request)

        assert got == expected
        mock_aenter.assert_called_once_with(user, got, request.session)
        mock_signal.assert_awaited_once_with(
            signal=workspace_requested,
            sender=Workspace,
            user=user,
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


def test_enter_workspace(settings: SettingsWrapper, client: Client) -> None:
    """Test if :func:`enter_workspace` changes the workspace and dispatch signals."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    workspace: Workspace = Workspace.objects.create(name="test workspace")
    session = client.session
    mock_signal = mock.Mock()

    workspace_entered.connect(mock_signal)
    try:
        enter_workspace(user, workspace, session)
    finally:
        workspace_entered.disconnect(mock_signal)

    mock_signal.assert_called_once_with(signal=workspace_entered, sender=Workspace, user=user, workspace=workspace)
    assert session[SESSION_KEY] == str(workspace.pk)


def test_enter_workspace_request(settings: SettingsWrapper, rf: RequestFactory, client: Client) -> None:
    """Test if :func:`enter_workspace` changes the workspace and dispatch signals."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    client.login(username="testuser", passworkd="testpw")
    request = rf.get("/")
    request.user = user
    request.session = client.session

    workspace: Workspace = Workspace.objects.create(name="test workspace")
    mock_signal = mock.Mock()

    workspace_entered.connect(mock_signal)
    try:
        enter_workspace(request, workspace)
    finally:
        workspace_entered.disconnect(mock_signal)

    mock_signal.assert_called_once_with(signal=workspace_entered, sender=Workspace, user=user, workspace=workspace)
    assert request.session[SESSION_KEY] == str(workspace.pk)


def test_enter_workspace_scope(settings: SettingsWrapper, client: Client) -> None:
    """Test if :func:`enter_workspace` changes the workspace and dispatch signals."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    session = client.session
    scope = {"user": user, "session": session}

    workspace: Workspace = Workspace.objects.create(name="test workspace")
    mock_signal = mock.Mock()

    workspace_entered.connect(mock_signal)
    try:
        enter_workspace(scope, workspace)
    finally:
        workspace_entered.disconnect(mock_signal)

    mock_signal.assert_called_once_with(signal=workspace_entered, sender=Workspace, user=user, workspace=workspace)
    assert session[SESSION_KEY] == str(workspace.pk)


def test_aenter_workspace(settings: SettingsWrapper, async_client: AsyncClient) -> None:
    """Test if :func:`aenter_workspace` changes the workspace and dispatch signals."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    workspace: Workspace = Workspace.objects.create(name="test workspace")
    session = async_client.session
    mock_signal = mock.AsyncMock()

    workspace_entered.connect(mock_signal)
    try:
        async_to_sync(aenter_workspace)(user, workspace, session)  # type: ignore[call-arg, arg-type]
    finally:
        workspace_entered.disconnect(mock_signal)

    mock_signal.assert_awaited_once_with(signal=workspace_entered, sender=Workspace, user=user, workspace=workspace)
    assert session[SESSION_KEY] == str(workspace.pk)


def test_aenter_workspace_request(
    settings: SettingsWrapper, async_rf: AsyncRequestFactory, async_client: AsyncClient
) -> None:
    """Test if :func:`aenter_workspace` changes the workspace and dispatch signals using a request."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    async_to_sync(async_client.alogin)(username="testuser", passworkd="testpw")
    request = async_rf.get("/")
    request.user = user
    request.session = async_client.session

    workspace: Workspace = Workspace.objects.create(name="test workspace")
    mock_signal = mock.AsyncMock()

    workspace_entered.connect(mock_signal)
    try:
        async_to_sync(aenter_workspace)(request, workspace)
    finally:
        workspace_entered.disconnect(mock_signal)

    mock_signal.assert_awaited_once_with(signal=workspace_entered, sender=Workspace, user=user, workspace=workspace)
    assert request.session[SESSION_KEY] == str(workspace.pk)


def test_aenter_workspace_scope(settings: SettingsWrapper, async_client: AsyncClient) -> None:
    """Test if :func:`aenter_workspace` changes the workspace and dispatch signals using a scope."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    session = async_client.session
    scope = {"user": user, "session": session}

    workspace: Workspace = Workspace.objects.create(name="test workspace")
    mock_signal = mock.AsyncMock()

    workspace_entered.connect(mock_signal)
    try:
        async_to_sync(aenter_workspace)(scope, workspace)  # type: ignore[arg-type]
    finally:
        workspace_entered.disconnect(mock_signal)

    mock_signal.assert_awaited_once_with(signal=workspace_entered, sender=Workspace, user=user, workspace=workspace)
    assert session[SESSION_KEY] == str(workspace.pk)


def test_leave_workspace(settings: SettingsWrapper, client: Client) -> None:
    """Test if :func:`leave_workspace` clears the workspace and dispatch signals."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    workspace: Workspace = Workspace.objects.create(name="test workspace")
    session = client.session
    session[SESSION_KEY] = str(workspace.pk)
    mock_signal = mock.Mock()

    workspace_exited.connect(mock_signal)
    try:
        leave_workspace(user, session)
    finally:
        workspace_exited.disconnect(mock_signal)

    mock_signal.assert_called_once_with(signal=workspace_exited, sender=Workspace, user=user, workspace=workspace)
    assert SESSION_KEY not in session


def test_leave_workspace_without_workspace(settings: SettingsWrapper, client: Client) -> None:
    """Test if :func:`leave_workspace` does nothing when no workspace is set."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    session = client.session
    session.pop(SESSION_KEY, None)
    mock_signal = mock.Mock()

    workspace_exited.connect(mock_signal)
    try:
        leave_workspace(user, session)
    finally:
        workspace_exited.disconnect(mock_signal)

    mock_signal.assert_not_called()
    assert SESSION_KEY not in session


def test_leave_workspace_request(settings: SettingsWrapper, rf: RequestFactory, client: Client) -> None:
    """Test if :func:`leave_workspace` clears the workspace and dispatch signals using a request."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    client.login(username="testuser", passworkd="testpw")
    workspace: Workspace = Workspace.objects.create(name="test workspace")
    request = rf.get("/")
    request.user = user
    request.session = client.session
    request.session[SESSION_KEY] = str(workspace.pk)
    mock_signal = mock.Mock()

    workspace_exited.connect(mock_signal)
    try:
        leave_workspace(request)
    finally:
        workspace_exited.disconnect(mock_signal)

    mock_signal.assert_called_once_with(signal=workspace_exited, sender=Workspace, user=user, workspace=workspace)
    assert SESSION_KEY not in request.session


def test_leave_workspace_scope(settings: SettingsWrapper, client: Client) -> None:
    """Test if :func:`leave_workspace` clears the workspace and dispatch signals using a scope."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    workspace: Workspace = Workspace.objects.create(name="test workspace")
    session = client.session
    session[SESSION_KEY] = str(workspace.pk)
    scope = {"user": user, "session": session}
    mock_signal = mock.Mock()

    workspace_exited.connect(mock_signal)
    try:
        leave_workspace(scope)
    finally:
        workspace_exited.disconnect(mock_signal)

    mock_signal.assert_called_once_with(signal=workspace_exited, sender=Workspace, user=user, workspace=workspace)
    assert SESSION_KEY not in session


def test_aleave_workspace(settings: SettingsWrapper, async_client: AsyncClient) -> None:
    """Test if :func:`aleave_workspace` clears the workspace and dispatch signals."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    workspace: Workspace = Workspace.objects.create(name="test workspace")
    session = async_client.session
    session[SESSION_KEY] = str(workspace.pk)
    mock_signal = mock.AsyncMock()

    workspace_exited.connect(mock_signal)
    try:
        async_to_sync(aleave_workspace)(user, session)  # type: ignore[call-arg, arg-type]
    finally:
        workspace_exited.disconnect(mock_signal)

    mock_signal.assert_awaited_once_with(signal=workspace_exited, sender=Workspace, user=user, workspace=workspace)
    assert SESSION_KEY not in session


def test_aleave_workspace_without_workspace(settings: SettingsWrapper, async_client: AsyncClient) -> None:
    """Test if :func:`aleave_workspace` does nothing when no workspace is set."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    session = async_client.session
    session.pop(SESSION_KEY, None)
    mock_signal = mock.AsyncMock()

    workspace_exited.connect(mock_signal)
    try:
        async_to_sync(aleave_workspace)(user, session)  # type: ignore[call-arg, arg-type]
    finally:
        workspace_exited.disconnect(mock_signal)

    mock_signal.assert_not_awaited()
    assert SESSION_KEY not in session


def test_aleave_workspace_request(
    settings: SettingsWrapper, async_rf: AsyncRequestFactory, async_client: AsyncClient
) -> None:
    """Test if :func:`aleave_workspace` clears the workspace and dispatch signals using a request."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    async_to_sync(async_client.alogin)(username="testuser", passworkd="testpw")
    workspace: Workspace = Workspace.objects.create(name="test workspace")
    request = async_rf.get("/")
    request.user = user
    request.session = async_client.session
    request.session[SESSION_KEY] = str(workspace.pk)
    mock_signal = mock.AsyncMock()

    workspace_exited.connect(mock_signal)
    try:
        async_to_sync(aleave_workspace)(request)
    finally:
        workspace_exited.disconnect(mock_signal)

    mock_signal.assert_awaited_once_with(signal=workspace_exited, sender=Workspace, user=user, workspace=workspace)
    assert SESSION_KEY not in request.session


def test_aleave_workspace_scope(settings: SettingsWrapper, async_client: AsyncClient) -> None:
    """Test if :func:`aleave_workspace` clears the workspace and dispatch signals using a scope."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    workspace: Workspace = Workspace.objects.create(name="test workspace")
    session = async_client.session
    session[SESSION_KEY] = str(workspace.pk)
    scope = {"user": user, "session": session}
    mock_signal = mock.AsyncMock()

    workspace_exited.connect(mock_signal)
    try:
        async_to_sync(aleave_workspace)(scope)  # type: ignore[arg-type]
    finally:
        workspace_exited.disconnect(mock_signal)

    mock_signal.assert_awaited_once_with(signal=workspace_exited, sender=Workspace, user=user, workspace=workspace)
    assert SESSION_KEY not in session


@mock.patch("django_workspaces.leave_workspace")
@mock.patch("django_workspaces.enter_workspace")
def test_switch_workspace(
    mock_enter_workspace: mock.Mock,
    mock_leave_workspace: mock.Mock,
    settings: SettingsWrapper,
    client: Client,
) -> None:
    """Test if :func:`switch_workspace` leaves the old workspace and enters the new one."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    workspace: Workspace = Workspace.objects.create(name="test workspace")
    session = client.session

    switch_workspace(user, workspace, session)

    mock_leave_workspace.assert_called_once_with(user, session)
    mock_enter_workspace.assert_called_once_with(user, workspace, session)


@mock.patch("django_workspaces.leave_workspace")
@mock.patch("django_workspaces.enter_workspace")
def test_switch_workspace_request(
    mock_enter_workspace: mock.Mock,
    mock_leave_workspace: mock.Mock,
    settings: SettingsWrapper,
    rf: RequestFactory,
    client: Client,
) -> None:
    """Test if :func:`switch_workspace` leaves the old workspace and enters the new one using a request."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    client.login(username="testuser", passworkd="testpw")
    request = rf.get("/")
    request.user = user
    request.session = client.session
    workspace: Workspace = Workspace.objects.create(name="test workspace")

    switch_workspace(request, workspace)

    mock_leave_workspace.assert_called_once_with(request, None)
    mock_enter_workspace.assert_called_once_with(request, workspace, None)


@mock.patch("django_workspaces.leave_workspace")
@mock.patch("django_workspaces.enter_workspace")
def test_switch_workspace_scope(
    mock_enter_workspace: mock.Mock,
    mock_leave_workspace: mock.Mock,
    settings: SettingsWrapper,
    client: Client,
) -> None:
    """Test if :func:`switch_workspace` leaves the old workspace and enters the new one using a scope."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    scope = {"user": user, "session": client.session}
    workspace: Workspace = Workspace.objects.create(name="test workspace")

    switch_workspace(scope, workspace)

    mock_leave_workspace.assert_called_once_with(scope, None)
    mock_enter_workspace.assert_called_once_with(scope, workspace, None)


@mock.patch("django_workspaces.aleave_workspace")
@mock.patch("django_workspaces.aenter_workspace")
def test_aswitch_workspace(
    mock_aenter_workspace: mock.AsyncMock,
    mock_aleave_workspace: mock.AsyncMock,
    settings: SettingsWrapper,
    async_client: AsyncClient,
) -> None:
    """Test if :func:`aswitch_workspace` leaves the old workspace and enters the new one."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    workspace: Workspace = Workspace.objects.create(name="test workspace")
    session = async_client.session

    async_to_sync(aswitch_workspace)(user, workspace, session)  # type: ignore[call-arg, arg-type]

    mock_aleave_workspace.assert_awaited_once_with(user, session)
    mock_aenter_workspace.assert_awaited_once_with(user, workspace, session)


@mock.patch("django_workspaces.aleave_workspace")
@mock.patch("django_workspaces.aenter_workspace")
def test_aswitch_workspace_request(
    mock_aenter_workspace: mock.AsyncMock,
    mock_aleave_workspace: mock.AsyncMock,
    settings: SettingsWrapper,
    async_rf: AsyncRequestFactory,
    async_client: AsyncClient,
) -> None:
    """Test if :func:`aswitch_workspace` leaves the old workspace and enters the new one using a request."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    async_to_sync(async_client.alogin)(username="testuser", passworkd="testpw")
    request = async_rf.get("/")
    request.user = user
    request.session = async_client.session
    workspace: Workspace = Workspace.objects.create(name="test workspace")

    async_to_sync(aswitch_workspace)(request, workspace)

    mock_aleave_workspace.assert_awaited_once_with(request, None)
    mock_aenter_workspace.assert_awaited_once_with(request, workspace, None)


@mock.patch("django_workspaces.aleave_workspace")
@mock.patch("django_workspaces.aenter_workspace")
def test_aswitch_workspace_scope(
    mock_aenter_workspace: mock.AsyncMock,
    mock_aleave_workspace: mock.AsyncMock,
    settings: SettingsWrapper,
    async_client: AsyncClient,
) -> None:
    """Test if :func:`aswitch_workspace` leaves the old workspace and enters the new one using a scope."""
    del settings.WORKSPACE_MODEL

    user = User.objects.create(username="testuser", email="test@example.com", password="testpw")  # noqa: S106
    scope = {"user": user, "session": async_client.session}
    workspace: Workspace = Workspace.objects.create(name="test workspace")

    async_to_sync(aswitch_workspace)(scope, workspace)  # type: ignore[arg-type]

    mock_aleave_workspace.assert_awaited_once_with(scope, None)
    mock_aenter_workspace.assert_awaited_once_with(scope, workspace, None)
