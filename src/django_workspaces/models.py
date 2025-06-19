"""Workspace models."""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django_stubs_ext.db.models import TypedModelMeta


class AbstractWorkspace(models.Model):
    """Abstract base class implementing a workspace.

    Custom workspace models should inherit from this class.
    """

    name = models.CharField(
        _("name"),
        max_length=255,
        help_text=_("Required. 255 characters or fewer."),
        db_comment="Workspace name",
    )

    class Meta(TypedModelMeta):
        abstract = True

    def __str__(self) -> str:
        """Return a string representation of the workspace."""
        return self.name


class Workspace(AbstractWorkspace):
    """Default workspace model."""

    class Meta(AbstractWorkspace.Meta):
        swappable = "WORKSPACE_MODEL"
