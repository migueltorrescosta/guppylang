import ast
from dataclasses import dataclass

from guppy.ast_util import AstNode, has_empty_body
from guppy.checker.core import Context, Globals
from guppy.checker.expr_checker import check_call, synthesize_call
from guppy.checker.func_checker import check_signature
from guppy.compiler.core import CompiledFunction, CompiledGlobals, DFContainer
from guppy.error import GuppyError
from guppy.gtypes import GuppyType, type_to_row
from guppy.hugr.hugr import Hugr, Node, OutPortV, VNode
from guppy.nodes import GlobalCall


@dataclass
class DeclaredFunction(CompiledFunction):
    """A user-declared function that compiles to a Hugr function declaration."""

    node: VNode | None = None

    @staticmethod
    def from_ast(
        func_def: ast.FunctionDef, name: str, globals: Globals
    ) -> "DeclaredFunction":
        ty = check_signature(func_def, globals)
        if not has_empty_body(func_def):
            raise GuppyError(
                "Body of function declaration must be empty", func_def.body[0]
            )
        return DeclaredFunction(name, ty, func_def, None)

    def check_call(
        self, args: list[ast.expr], ty: GuppyType, node: AstNode, ctx: Context
    ) -> GlobalCall:
        # Use default implementation from the expression checker
        args = check_call(self.ty, args, ty, node, ctx)
        return GlobalCall(func=self, args=args)

    def synthesize_call(
        self, args: list[ast.expr], node: AstNode, ctx: Context
    ) -> tuple[GlobalCall, GuppyType]:
        # Use default implementation from the expression checker
        args, ty = synthesize_call(self.ty, args, node, ctx)
        return GlobalCall(func=self, args=args), ty

    def add_to_graph(self, graph: Hugr, parent: Node) -> None:
        self.node = graph.add_declare(self.ty, parent, self.name)

    def load(
        self, dfg: DFContainer, graph: Hugr, globals: CompiledGlobals, node: AstNode
    ) -> OutPortV:
        assert self.node is not None
        return graph.add_load_constant(self.node.out_port(0), dfg.node).out_port(0)

    def compile_call(
        self,
        args: list[OutPortV],
        dfg: DFContainer,
        graph: Hugr,
        globals: CompiledGlobals,
        node: AstNode,
    ) -> list[OutPortV]:
        assert self.node is not None
        call = graph.add_call(self.node.out_port(0), args, dfg.node)
        return [call.out_port(i) for i in range(len(type_to_row(self.ty.returns)))]