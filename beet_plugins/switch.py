from dataclasses import dataclass
from typing import Any, cast

from beet import Context
from beet.core.utils import required_field
from bolt import Accumulator, Runtime, visit_body, visit_generic, visit_single
from bolt_expressions import Source
from mecha import (
    AlternativeParser,
    AstChildren,
    AstCommand,
    AstNode,
    AstRoot,
    CommandTree,
    Mecha,
    Visitor,
    consume_line_continuation,
    delegate,
    rule,
)
from tokenstream import InvalidSyntax, TokenStream, set_location

COMMAND_TREE = {
    "type": "root",
    "children": {
        "switch": {
            "type": "literal",
            "children": {
                "source": {
                    "type": "argument",
                    "parser": "bolt_expressions:source",
                    "children": {
                        "body": {
                            "type": "argument",
                            "parser": "bolt_expressions:switch_root",
                            "executable": True,
                        },
                    },
                },
            },
        },
    },
}


def beet_default(ctx: Context):
    ctx.inject(switch)


def switch(ctx: Context):
    mc = ctx.inject(Mecha)

    mc.spec.add_commands(CommandTree.parse_obj(COMMAND_TREE))

    mc.spec.parsers["switch_root"] = parse_switch_root
    mc.spec.parsers["switch_case"] = parse_switch_case
    mc.spec.parsers["switch_case_value"] = AlternativeParser(
        [
            delegate("command:argument:bolt_expressions:source"),
            delegate("integer_range"),
        ]
    )
    mc.spec.parsers["command:argument:bolt_expressions:switch_root"] = delegate(
        "switch_root"
    )

    runtime = ctx.inject(Runtime)

    runtime.modules.codegen.extend(SwitchCodegen())

    runtime.helpers["emit_switch"] = SwitchConverter()


@dataclass(frozen=True, slots=True)
class AstSwitchCase(AstNode):
    """Ast switch case node."""

    test: AstNode = required_field()
    inverted: bool = required_field()
    body: AstRoot = required_field()

    parser = "switch_case"


@dataclass(frozen=True, slots=True)
class AstSwitchRoot(AstNode):
    """Ast switch root node."""

    cases: AstChildren[AstSwitchCase] = required_field()

    parser = "switch_root"


def parse_switch_case(stream: TokenStream):
    with stream.syntax(case=r"case\b", invert=r"not\b"):
        case = stream.expect("case")
        inverted = stream.get("invert")
        test = delegate("switch_case_value", stream)
        body: AstRoot = delegate("nested_root", stream)

        case_node = AstSwitchCase(test=test, inverted=inverted is not None, body=body)
        return set_location(case_node, location=case, end_location=body)


def parse_switch_root(stream: TokenStream):
    with stream.syntax(colon=r":"):
        colon = stream.expect("colon")

    if not consume_line_continuation(stream):
        exc = InvalidSyntax("Expected non-empty block.")
        raise set_location(exc, colon)

    cases: list[AstSwitchCase] = []

    while True:
        cases.append(delegate("switch_case", stream))

        if not consume_line_continuation(stream):
            break

    node = AstSwitchRoot(cases=AstChildren(cases))
    return set_location(node, location=colon, end_location=cases[-1])


class SwitchCodegen(Visitor):
    @rule(AstCommand, identifier="switch:source:body")
    def switch(self, node: AstCommand, acc: Accumulator):
        print("codegen switch")
        source = yield from visit_single(node.arguments[0], required=True)

        switch = cast(AstSwitchRoot, node.arguments[1])
        for case in switch.cases:
            test = yield from visit_single(case.test)
            if test is None:
                test = acc.make_ref(case.test)

            body = yield from visit_generic(case.body, acc)
            if body is None:
                body = acc.make_ref(case.body)

            print("emit_switch", source, test, case.inverted, body)

            rhs = acc.helper("emit_switch", source, test, case.inverted, body)
            acc.statement(rhs)
            print("cuuu")

        return []


class SwitchConverter:
    def __call__(self, source: Source, test: Any, inverted: bool, body: AstRoot):
        print("switch converter:", source, test, inverted, body)
