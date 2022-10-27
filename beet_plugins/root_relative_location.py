"""Plugin that resolves root-relative resource locations."""


__all__ = [
    "AstRootResourceLocation",
    "resolve_root_resource_location",
    "root_relative_location",
    "RootRelativeLocationCodegen",
    "RootRelativeLocationParser",
]


from dataclasses import dataclass
from functools import partial

from beet import Context, Generator
from bolt import Accumulator, Runtime
from tokenstream import TokenStream, set_location
from mecha import (
    AstResourceLocation,
    CommentDisambiguation,
    Mecha,
    Parser,
    Visitor,
    rule,
)


PATTERN = r"#?~/[0-9a-z_./-]+"


def beet_default(ctx: Context):
    ctx.require(root_relative_location)


def root_relative_location(ctx: Context):
    mc = ctx.inject(Mecha)
    runtime = ctx.inject(Runtime)

    parsers = mc.spec.parsers

    parsers["resource_location_or_tag"] = CommentDisambiguation(
        RootRelativeLocationParser(parser=parsers["resource_location_or_tag"])
    )

    parsers["bolt:literal"] = RootRelativeLocationParser(parser=parsers["bolt:literal"])

    runtime.helpers["resolve_root_resource_location"] = partial(
        resolve_root_resource_location, ctx.generate
    )

    runtime.modules.codegen.extend(RootRelativeLocationCodegen())


def resolve_root_resource_location(gen: Generator, path: str, is_tag: bool = False):
    path = gen.path(path)
    return "#" + path if is_tag else path


@dataclass(frozen=True)
class AstRootResourceLocation(AstResourceLocation):
    ...


@dataclass
class RootRelativeLocationParser:
    """Parser that resolves root-relative resource locations."""

    parser: Parser

    def __call__(self, stream: TokenStream) -> AstResourceLocation:
        with stream.syntax(root_resource_location=PATTERN):
            token = stream.get("root_resource_location")

            if token is None:
                return self.parser(stream)

            is_tag = token.value.startswith("#")
            path = token.value[3:] if is_tag else token.value[2:]

            node = AstRootResourceLocation(is_tag=is_tag, path=path)

            return set_location(node, token)


@dataclass
class RootRelativeLocationCodegen(Visitor):
    @rule(AstRootResourceLocation)
    def root_location(self, node: AstRootResourceLocation, acc: Accumulator):
        result = acc.make_variable()
        value = acc.helper("resolve_root_resource_location", f"{node.path!r}", node.is_tag)
        acc.statement(f"{result} = {value}", lineno=node)

        return [result]
