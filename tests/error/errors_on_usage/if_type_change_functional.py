from tests.error.util import guppy


@guppy
def foo(x: bool) -> int:
    y = 3
    _@functional
    if x:
        y = False
    return y