"""Plugin that resolves root resource locations."""


__all__ = [
    "AstRootResourceLocation",
    "beet_default",
    "resolve_root_resource_location",
    "root_location",
    "RootLocationCodegen",
    "RootLocationParser",
]


from dataclasses import dataclass
from functools import partial

from beet import Context, Generator
from bolt import Accumulator, InterpolationParser, Runtime
from mecha import (
    AlternativeParser,
    AstResourceLocation,
    CommentDisambiguation,
    Mecha,
    Parser,
    Visitor,
    rule,
)
from tokenstream import TokenStream, set_location

PATTERN = r"#?/[0-9a-z_./-]*"


def beet_default(ctx: Context):
    ctx.require(root_location)


def root_location(ctx: Context):
    mc = ctx.inject(Mecha)
    runtime = ctx.inject(Runtime)

    parsers = mc.spec.parsers

    parsers["resource_location_or_tag"] = AlternativeParser(
        [
            InterpolationParser("resource_location"),
            CommentDisambiguation(
                RootLocationParser(parser=parsers["resource_location_or_tag"])
            ),
        ]
    )
    parsers["bolt:literal"] = RootLocationParser(
        parser=parsers["bolt:literal"], literal=True
    )
    parsers["bolt:import"] = RootLocationParser(
        parsers["bolt:import"], generate=ctx.generate
    )

    runtime.helpers["resolve_root_resource_location"] = partial(
        resolve_root_resource_location, ctx.generate
    )

    runtime.modules.codegen.extend(RootLocationCodegen())


@dataclass(frozen=True)
class AstRootResourceLocation(AstResourceLocation):
    """Ast root resource location node."""

    literal: bool = False


@dataclass
class RootLocationParser:
    """
    Parser that resolves root resource locations.

    `generate`: A `Generator` object. If provided, root resource
    locations are resolved during parsing.

    `literal`: A flag. If true, the parsed `AstRootResourceLocation` node
    will be treated like a literal value during codegen, being resolved to a
    plain string instead of a `AstResourceLocation` node.
    """

    parser: Parser
    generate: Generator | None = None
    literal: bool = False

    def __call__(self, stream: TokenStream) -> AstResourceLocation:
        with stream.syntax(root_resource_location=PATTERN):
            token = stream.get("root_resource_location")

            if token is None:
                return self.parser(stream)

            is_tag = token.value.startswith("#")
            path = token.value[2:] if is_tag else token.value[1:]

            if self.generate:
                full_path = self.generate.path(path)
                namespace, _, path = full_path.rpartition(":")
                node = AstResourceLocation(
                    is_tag=is_tag, namespace=namespace, path=path
                )
            else:
                node = AstRootResourceLocation(
                    is_tag=is_tag, path=path, literal=self.literal
                )

            return set_location(node, token)


@dataclass
class RootLocationCodegen(Visitor):
    @rule(AstRootResourceLocation)
    def root_location(self, node: AstRootResourceLocation, acc: Accumulator):
        result = acc.make_variable()
        value = acc.helper(
            "resolve_root_resource_location", f"{node.path!r}", node.is_tag
        )
        acc.statement(f"{result} = {value}", lineno=node)

        if not node.literal:
            rhs = acc.helper(
                "interpolate_resource_location", result, acc.make_ref(node)
            )
            acc.statement(f"{result} = {rhs}")

        return [result]


def resolve_root_resource_location(
    gen: Generator, path: str, is_tag: bool = False
) -> str:
    path = gen.path(path)
    return "#" + path if is_tag else path
