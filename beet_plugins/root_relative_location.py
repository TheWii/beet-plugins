"""Plugin that resolves root-relative resource locations."""


__all__ = [
    "RootRelativeLocationParser",
    "RootRelativeLocationLiteralParser",
    "resolve_using_database",
]


from dataclasses import dataclass

from beet import Context
from bolt import AstValue
from tokenstream import TokenStream, set_location
from mecha import (
    AstResourceLocation,
    CommentDisambiguation,
    Mecha,
    Parser,
)


PATTERN = r"#?~/[0-9a-z_./-]+"


def beet_default(ctx: Context):
    mc = ctx.inject(Mecha)
    parsers = mc.spec.parsers
    parsers["resource_location_or_tag"] = CommentDisambiguation(
        RootRelativeLocationParser(parser=parsers["resource_location_or_tag"], ctx=ctx)
    )
    parsers["bolt:literal"] = RootRelativeLocationLiteralParser(
        parser=parsers["bolt:literal"], ctx=ctx
    )


@dataclass
class RootRelativeLocationParser:
    """Parser that resolves root-relative resource locations."""

    parser: Parser
    ctx: Context

    def __call__(self, stream: TokenStream) -> AstResourceLocation:
        with stream.syntax(root_resource_location=PATTERN):
            token = stream.get("root_resource_location")

            if token is None:
                return self.parser(stream)

            is_tag = token.value.startswith("#")
            value = token.value[3:] if is_tag else token.value[2:]
            full_path = self.ctx.generate.path(value)
            namespace, _, path = full_path.rpartition(":")

            node = AstResourceLocation(is_tag=is_tag, namespace=namespace, path=path)
            return set_location(node, token)


@dataclass
class RootRelativeLocationLiteralParser:
    parser: Parser
    ctx: Context

    def __call__(self, stream: TokenStream) -> AstValue:
        with stream.syntax(root_resource_location=PATTERN):
            token = stream.get("root_resource_location")

            if token is None:
                return self.parser(stream)

            is_tag = token.value.startswith("#")
            stripped = token.value[3:] if is_tag else token.value[2:]
            value = "#" * is_tag + self.ctx.generate.path(stripped)

            node = AstValue(value=value)
            return set_location(node, token)
