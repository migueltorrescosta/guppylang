from tests.error.util import guppy


@guppy
def foo() -> int:
    a, b = 1, True, 3.0
    return a