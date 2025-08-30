"""Tests for WorkspaceMiddleware."""

from unittest import mock

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured

from django_workspaces.contrib.channels import WorkspaceMiddleware


@pytest.mark.asyncio
class TestWorkspaceMiddleware:  # noqa: D101
    async def test_without_session_fails(self) -> None:
        """Teste if requires SessionMiddleware."""
        inner = mock.AsyncMock()

        app = WorkspaceMiddleware(inner)

        with pytest.raises(ImproperlyConfigured, match="SessionMiddleware"):
            await app({}, mock.AsyncMock(), mock.AsyncMock())

        inner.assert_not_awaited()

    async def test_without_auth_middleware_fails(self) -> None:
        """Test if requires SessionMiddleware."""
        inner = mock.AsyncMock()

        app = WorkspaceMiddleware(inner)

        with pytest.raises(ImproperlyConfigured, match="AuthMiddleware"):
            await app({"session": "something"}, mock.AsyncMock(), mock.AsyncMock())

        inner.assert_not_awaited()

    async def test_resolves_workspace(self, admin_user: User) -> None:
        """Test if resolves user workspace."""
        inner = mock.AsyncMock()

        app = WorkspaceMiddleware(inner)

        expected = mock.Mock()

        with mock.patch(
            "django_workspaces.contrib.channels.middleware.aresolve_workspace", return_value=expected
        ) as mock_aresolve:
            await app({"user": admin_user, "session": "something"}, mock.AsyncMock(), mock.AsyncMock())

        mock_aresolve.assert_awaited_once_with(admin_user, "something")
        inner.assert_awaited_once()
