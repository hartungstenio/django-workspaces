import sys

if sys.version_info >= (3, 12):
    from inspect import iscoroutinefunction, markcoroutinefunction
    from typing import override
else:
    from asgiref.sync import iscoroutinefunction, markcoroutinefunction
    from typing_extensions import override

if sys.version_info >= (3, 13):
    from typing import TypeIs
else:
    from typing_extensions import TypeIs

__all__ = [
    "TypeIs",
    "iscoroutinefunction",
    "markcoroutinefunction",
    "override",
]
