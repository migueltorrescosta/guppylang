import tests.error.util

from guppy.compiler import GuppyModule
from tests.error.util import NonBool

module = GuppyModule("test")
module.load(tests.error.util)


@module
def foo(x: bool, y: NonBool) -> bool:
    return x or y


module.compile(True)