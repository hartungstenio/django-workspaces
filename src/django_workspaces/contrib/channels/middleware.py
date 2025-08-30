"""channels-compatible workspace middleware."""

from collections.abc import Mapping
from typing import Any

from asgiref.typing import ASGIApplication, ASGIReceiveCallable, ASGISendCallable
from channels.auth import AuthMiddlewareStack
from channels.middleware import BaseMiddleware
from django.core.exceptions import ImproperlyConfigured

from django_workspaces import aresolve_workspace
from django_workspaces._compat import override


class WorkspaceMiddleware(BaseMiddleware):
    """
    Middleware which populates scope["workspace"] from a Django session.

    Requires both AuthMiddleware and SessionMiddleware to function.
    """

    @override
    async def __call__(
        self, scope: Mapping[str, Any], receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> ASGIApplication:
        """Call the middleware.

        Inserts a ^workspace^ key into the scope.
        """
        if "session" not in scope:
            msg: str = "WorkspaceMiddleware cannot find session in scope. SessionMiddleware must be above it."
            raise ImproperlyConfigured(msg)

        if "user" not in scope:
            msg = "WorkspaceMiddleware cannot find user in scope. AuthMiddleware must be above it."
            raise ImproperlyConfigured(msg)

        if "workspace" not in scope:
            scope = dict(scope)
            scope["workspace"] = await aresolve_workspace(scope["user"], scope["session"])

        return await super().__call__(scope, receive, send)  # type: ignore[arg-type]


def WorkspaceMiddlewareStack(inner: ASGIApplication) -> ASGIApplication:  # noqa: N802
    """Shortcut for applying all layers at once."""
    return AuthMiddlewareStack(WorkspaceMiddleware(inner))
