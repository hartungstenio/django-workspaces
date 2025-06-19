"""Tests for module functions."""

from django.apps import apps
from pytest_django.fixtures import SettingsWrapper

from django_workspaces import get_workspace_model
from django_workspaces.models import Workspace


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
