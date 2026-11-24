# Project Guidelines

## Project Structure

- Application code lives in `src/django_workspaces/`.
- Tests live in `tests/` and use the Django project in `demo/`.
- The package supports both synchronous and asynchronous middleware, workspace resolution, and Channels behavior; keep paired APIs aligned when changing shared behavior.
- Database schema changes require a new migration under `src/django_workspaces/migrations/`.

## Development Commands

- Run the full test matrix with `hatch test`.
- Run focused tests with `hatch run pytest tests/<test_file>.py`.
- Run code quality checks with `hatch check code`.
- Verify formatting with `hatch check fmt`.
- Run strict type checks with `hatch check types`.
- Check direct dependencies with `hatch run deptry . --github-output`.
- Generate migrations with `hatch run python manage.py makemigrations django_workspaces -n "friendly_name"`; never hand-write migrations.

## Python and Django Conventions

- Support the Python and Django versions declared in `pyproject.toml`, including Python 3.15.
- Preserve strict typing and existing type annotations; production code is checked with mypy and Pyrefly.
- Follow the existing Ruff configuration, including a 120-character line limit.
- Use Django ORM, authentication, permissions, and settings APIs rather than duplicating framework behavior.
- Read Django settings through the project's existing accessors or Django's `settings` object consistently with neighboring code.
- Use timezone-aware datetimes through `django.utils.timezone` where applicable.
- Keep synchronous and asynchronous public APIs behaviorally equivalent.
- Preserve compatibility with Django 5.2, 6.0, and 6.1 as declared in the support matrix.

## Testing Expectations

- Add or update focused tests for every behavior change.
- Include both synchronous and asynchronous coverage when changing a paired API.
- Run the focused test file first, then the full suite before finishing.
- Keep test classes and methods grouped and ordered consistently with neighboring tests and corresponding source definitions.
- Cover middleware behavior with and without authenticated sessions and for sync/async paths where applicable.

## Change Scope

- Keep changes minimal and consistent with neighboring code.
- Do not modify generated migration history or unrelated user changes.
- Use Conventional Commits for commit messages, such as `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, or `chore:`.
- Update `README.md` when a change affects documented behavior, public APIs, configuration, installation, or usage.
- Update `CHANGELOG.md` for user-visible changes that are not yet part of a published release.
