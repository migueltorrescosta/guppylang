from tests.error.util import guppy


@guppy
def foo(x: bool) -> int:
    while x:
        return 42
        x = 42