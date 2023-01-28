"""Debounce help module."""
# from collections.abc import Callable
# from threading import Timer
# from typing import Any


# def debounce(wait: int):
#     """Debounce main method."""

#     def decorator(callable_function: Callable):
#         def debounced(*args: Any, **kwargs: Any):
#             def call_it() -> None:
#                 callable_function(*args, **kwargs)

#             try:
#                 debounced.timer.cancel()
#             except (AttributeError):
#                 pass
#             debounced.timer = Timer(wait, call_it)
#             debounced.timer.start()

#         return debounced

#     return decorator
