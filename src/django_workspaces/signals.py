"""Dispatched signals."""

from django.dispatch import Signal

workspace_requested = Signal()
"""Dispatched when a workspace is not found in the current session.

This should look up the user's preferences to get the latest or default workspace.

Args:
    sender: The current workspace model.
    user: The user requesting a workspace.
    request: The current request. Optional.

Returns:
    A workspace instance if could find a default workspace. None otherwise.
"""
