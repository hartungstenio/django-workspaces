# django-workspaces

[![PyPI - Version](https://img.shields.io/pypi/v/django-workspaces.svg)](https://pypi.org/project/django-workspaces)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-workspaces.svg)](https://pypi.org/project/django-workspaces)

Multi-workspace support for Django. Allows users to switch between isolated workspaces within the same application, with full sync and async support.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Accessing the workspace in views](#accessing-the-workspace-in-views)
  - [Entering and leaving workspaces](#entering-and-leaving-workspaces)
  - [Resolving a workspace manually](#resolving-a-workspace-manually)
- [Signals](#signals)
  - [Setting a default workspace](#setting-a-default-workspace)
- [Custom workspace model](#custom-workspace-model)
- [Django Channels](#django-channels)
- [Object-level permissions](#object-level-permissions)
- [Header-based resolution](#header-based-resolution)
- [Type hints](#type-hints)
- [License](#license)

---

## Installation

```console
pip install django-workspaces
```

## Quick Start

**1. Add to `INSTALLED_APPS` and configure the middleware:**

```python
# settings.py

INSTALLED_APPS = [
    ...
    "django_workspaces",
]

MIDDLEWARE = [
    ...
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_workspaces.middleware.workspace_middleware",  # after auth
]
```

**2. Run migrations:**

```console
python manage.py migrate
```

**3. Create workspaces and assign them to users, then use `request.workspace` in your views.**

---

## Configuration

All settings are optional and go in `settings.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `WORKSPACE_MODEL` | `"django_workspaces.Workspace"` | Swappable workspace model — see [Custom workspace model](#custom-workspace-model) |
| `WORKSPACE_ID_HEADER` | `None` | HTTP header used to resolve the workspace by ID — see [Header-based resolution](#header-based-resolution) |
| `WORKSPACE_CHECK_OBJECT_PERMISSIONS` | `False` | Enforce `view_<model>` object-level permission when entering a workspace — see [Object-level permissions](#object-level-permissions) |

---

## Usage

### Accessing the workspace in views

After adding the middleware, every request has a `workspace` property:

```python
# views.py

def dashboard(request):
    workspace = request.workspace  # raises Http404 if none found
    return render(request, "dashboard.html", {"workspace": workspace})
```

For async views:

```python
async def dashboard(request):
    workspace = await request.aworkspace()
    return render(request, "dashboard.html", {"workspace": workspace})
```

### Entering and leaving workspaces

Use `enter_workspace` to set the active workspace for a user and `leave_workspace` to unset it.

```python
from django_workspaces import enter_workspace, leave_workspace, switch_workspace

# Enter a workspace — accepts a request, an ASGI scope, or (user, workspace, session)
def select_workspace(request, workspace_id):
    workspace = get_object_or_404(Workspace, pk=workspace_id)
    enter_workspace(request, workspace=workspace)
    return redirect("dashboard")

# Leave the current workspace
def deselect_workspace(request):
    leave_workspace(request)
    return redirect("home")

# Switch directly from one workspace to another
def switch(request, workspace_id):
    workspace = get_object_or_404(Workspace, pk=workspace_id)
    switch_workspace(request, workspace=workspace)
    return redirect("dashboard")
```

Async equivalents are available as `aenter_workspace`, `aleave_workspace`, and `aswitch_workspace`:

```python
from django_workspaces import aenter_workspace, aleave_workspace

async def select_workspace(request, workspace_id):
    workspace = await Workspace.objects.aget(pk=workspace_id)
    await aenter_workspace(request, workspace=workspace)
    return redirect("dashboard")
```

All three functions also accept `(user, workspace, session)` directly, which is useful outside of a request/response cycle:

```python
enter_workspace(request.user, workspace=workspace, session=request.session)
```

### Resolving a workspace manually

`get_workspace` resolves the active workspace from a request without the middleware:

```python
from django_workspaces import get_workspace

def my_view(request):
    workspace = get_workspace(request)
    ...
```

`resolve_workspace` accepts a user and session directly:

```python
from django_workspaces import resolve_workspace

workspace = resolve_workspace(user, session)
```

---

## Signals

`django_workspaces` exposes three signals:

| Signal | Sent when | Key arguments |
|--------|-----------|---------------|
| `workspace_requested` | No workspace in session; a default is being looked up | `user`, `request` (optional) |
| `workspace_entered` | User enters a workspace | `user`, `workspace` |
| `workspace_exited` | User leaves a workspace | `user`, `workspace` |

### Setting a default workspace

Connect to `workspace_requested` to automatically assign a workspace when none is set in the session. The signal expects the handler to return a workspace instance (or `None`):

```python
# apps.py

from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        from django_workspaces.signals import workspace_requested
        workspace_requested.connect(get_default_workspace)

def get_default_workspace(sender, user, **kwargs):
    """Return the first workspace the user has access to."""
    return sender.objects.filter(members=user).first()
```

A common use case is persisting the last workspace a user visited, so it can be restored on their next session. Connect `workspace_entered` to save the preference and `workspace_requested` to restore it:

```python
# myapp/models.py

class WorkspacePreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workspace_preference",
    )
    last_workspace = models.ForeignKey(
        settings.WORKSPACE_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
```

```python
# myapp/apps.py

from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        from django_workspaces.signals import workspace_entered, workspace_requested
        workspace_entered.connect(save_last_workspace)
        workspace_requested.connect(restore_last_workspace)

def save_last_workspace(sender, user, workspace, **kwargs):
    """Persist the workspace the user just entered."""
    WorkspacePreference.objects.update_or_create(
        user=user,
        defaults={"last_workspace": workspace},
    )

def restore_last_workspace(sender, user, **kwargs):
    """Return the last workspace the user visited, if any."""
    pref = WorkspacePreference.objects.filter(user=user).select_related("last_workspace").first()
    return pref.last_workspace if pref else None
```

With this setup, the first time a user makes a request without a workspace in their session, `workspace_requested` fires and `restore_last_workspace` returns their previous workspace automatically.

---

## Custom workspace model

To add fields to the workspace, define a custom model and point `WORKSPACE_MODEL` to it — similar to `AUTH_USER_MODEL`.

```python
# myapp/models.py

from django_workspaces.models import AbstractWorkspace

class Project(AbstractWorkspace):
    slug = models.SlugField(unique=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="projects",
    )

    class Meta(AbstractWorkspace.Meta):
        pass
```

```python
# settings.py

WORKSPACE_MODEL = "myapp.Project"
```

Then run `python manage.py makemigrations` and `python manage.py migrate`.

> **Note:** `WORKSPACE_MODEL` must be set before the first migration is run, just like `AUTH_USER_MODEL`.

To retrieve the active workspace model at runtime:

```python
from django_workspaces import get_workspace_model

Workspace = get_workspace_model()
```

---

## Django Channels

For WebSocket or other ASGI consumers, install the Channels extra:

```console
pip install django-workspaces[channels]
```

Use `WorkspaceMiddlewareStack` in your ASGI routing:

```python
# asgi.py

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django_workspaces.contrib.channels.middleware import WorkspaceMiddlewareStack

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": WorkspaceMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

The workspace is then available on the scope:

```python
class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        workspace = self.scope["workspace"]
        ...
```

`WorkspaceMiddlewareStack` is a shortcut for `AuthMiddlewareStack(WorkspaceMiddleware(inner))`. If you need finer control, compose the middleware manually:

```python
from channels.auth import AuthMiddlewareStack
from channels.sessions import SessionMiddlewareStack
from django_workspaces.contrib.channels.middleware import WorkspaceMiddleware

application = ProtocolTypeRouter({
    "websocket": SessionMiddlewareStack(
        AuthMiddlewareStack(
            WorkspaceMiddleware(
                URLRouter(websocket_urlpatterns)
            )
        )
    ),
})
```

---

## Object-level permissions

Enable `WORKSPACE_CHECK_OBJECT_PERMISSIONS` to require users to have the `view_<model>` object permission before entering a workspace:

```python
# settings.py

WORKSPACE_CHECK_OBJECT_PERMISSIONS = True
```

With this enabled, `enter_workspace` (and its async variant) raises `PermissionDenied` if the user does not have the `view_workspace` permission on the target workspace. The permission codename follows Django's convention: `{app_label}.view_{model_name}`.

This works with any Django-compatible permission backend, including [django-guardian](https://django-guardian.readthedocs.io/) for row-level permissions:

```python
from guardian.shortcuts import assign_perm

# Grant a user access to a specific workspace
assign_perm("view_workspace", user, workspace)
```

---

## Header-based resolution

For API scenarios where the client specifies the workspace per request, configure `WORKSPACE_ID_HEADER`:

```python
# settings.py

WORKSPACE_ID_HEADER = "x-workspace-id"
```

When set, `get_workspace` (and `request.workspace`) will look for this header first and resolve the workspace by its primary key. Session-based resolution is used as a fallback.

```http
GET /api/data/ HTTP/1.1
X-Workspace-Id: 42
```

> **Note:** Header-based resolution is a read-only lookup — it does **not** call `enter_workspace` internally. As a consequence, the `workspace_entered` and `workspace_exited` signals are **not** fired for requests that resolve the workspace through the header. If your application relies on those signals (e.g. to track the last visited workspace), prefer session-based resolution or call `enter_workspace` explicitly in your authentication flow.

---

## Type hints

When using the middleware, import the enhanced request type for accurate type checking:

```python
from django_workspaces.types import HttpRequest

def my_view(request: HttpRequest):
    workspace = request.workspace  # typed as AbstractWorkspace
```

---

## License

`django-workspaces` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
