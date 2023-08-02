from abc import ABC
from dataclasses import dataclass
from typing import Iterator, Optional, Any

from guppy.ast_util import AstNode
from guppy.guppy_types import GuppyType
from guppy.hugr.hugr import OutPortV, Hugr, DFContainingNode


@dataclass
class RawVariable:
    """Class holding data associated with a variable.

    Besides the name and type, we also store an AST node where the variable was defined.
    """

    name: str
    ty: GuppyType
    defined_at: AstNode

    def __lt__(self, other: Any) -> bool:
        # We define an ordering on variables that is used to determine in which order
        # they are outputted from basic blocks. We need to output linear variables at
        # the end, so we do a lexicographic ordering of linearity and name, exploiting
        # the fact that `False < True` in Python.
        if not isinstance(other, Variable):
            return NotImplemented
        return (self.ty.linear, self.name) < (other.ty.linear, other.name)


@dataclass
class Variable(RawVariable):
    """Represents a concrete variable during compilation.

    Compared to a `RawVariable`, each variable corresponds to a Hugr port.
    """

    port: OutPortV
    used: Optional[AstNode] = None

    def __init__(self, name: str, port: OutPortV, defined_at: AstNode):
        super().__init__(name, port.ty, defined_at)
        object.__setattr__(self, "port", port)


# A dictionary mapping names to live variables
VarMap = dict[str, Variable]


@dataclass
class DFContainer:
    """A dataflow graph under construction.

    This class is passed through the entire compilation pipeline and stores the node
    whose dataflow child-graph is currently being constructed as well as all live
    variables. Note that the variable map is mutated in-place and always reflects the
    current compilation state.
    """

    node: DFContainingNode
    variables: VarMap

    def __getitem__(self, item: str) -> Variable:
        return self.variables[item]

    def __setitem__(self, key: str, value: Variable) -> None:
        self.variables[key] = value

    def __iter__(self) -> Iterator[Variable]:
        return iter(self.variables.values())

    def __contains__(self, item: str) -> bool:
        return item in self.variables

    def __copy__(self) -> "DFContainer":
        # Make a copy of the var map so that mutating the copy doesn't
        # mutate our variable mapping
        return DFContainer(self.node, self.variables.copy())

    def get_var(self, name: str) -> Optional[Variable]:
        return self.variables.get(name, None)


class CompilerBase(ABC):
    """Base class for the Guppy compiler."""

    graph: Hugr
    global_variables: VarMap

    def __init__(self, graph: Hugr, global_variables: VarMap) -> None:
        self.graph = graph
        self.global_variables = global_variables


def return_var(n: int) -> str:
    """Name of the dummy variable for the n-th return value of a function.

    During compilation, we treat return statements like assignments of dummy variables.
    For example, the statement `return e0, e1, e2` is treated like `%ret0 = e0 ; %ret1 =
    e1 ; %ret2 = e2`. This way, we can reuse our existing mechanism for passing of live
    variables between basic blocks."""
    return f"%ret{n}"