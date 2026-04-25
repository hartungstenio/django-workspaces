from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class WorkspacePreference(models.Model):
    """Model to store the user's latest workspace."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workspace_preference",
        verbose_name=_("user"),
        help_text=_("User this preference belongs to"),
        db_comment="User this preference belongs to",
    )
    last_workspace = models.ForeignKey(
        settings.WORKSPACE_MODEL,
        on_delete=models.SET_NULL,
        verbose_name=_("last used workspace"),
        help_text=_("Last workspace the user used"),
        db_comment="Last workspace the user used",
    )

    def __str__(self) -> str:
        """Return a string representation of the workspace."""
        return f"{self.user_id}"
