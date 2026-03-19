# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-03-19

### Added

- Preferences app to store the last active workspace per user
- Object-level permission enforcement on workspace entry
- Support for resolving workspace from request header when `WORKSPACE_ID_HEADER` is configured
- README with usage examples, configuration reference, signals guide, custom workspace model, Django Channels, and type hints

## [0.1.0] - 2026-03-05

### Added

- Routines to enter and leave a workspace (`enter_workspace` / `leave_workspace`)
- Django Channels middleware for workspace resolution

## [0.0.1a1] - 2025-07-02

### Added

- Workspace models
- Workspace middleware for Django WSGI/ASGI applications
- `get_workspace` helper to retrieve the active workspace from a request

[Unreleased]: https://github.com/hartungstenio/django-workspaces/compare/0.2.0...HEAD
[0.2.0]: https://github.com/hartungstenio/django-workspaces/compare/0.1.0...0.2.0
[0.1.0]: https://github.com/hartungstenio/django-workspaces/compare/0.0.1a1...0.1.0
[0.0.1a1]: https://github.com/hartungstenio/django-workspaces/releases/tag/0.0.1a1
