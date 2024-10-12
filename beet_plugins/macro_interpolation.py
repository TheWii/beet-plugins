"""Plugin for activating bolt interpolation in mcfunction macros."""

__all__ = ["macro_interpolation"]

from mecha import Mecha, AlternativeParser, AstMacroLineText
from bolt import Runtime, InterpolationParser
from bolt.helpers import converter
from beet import Context


def macro_interpolation(ctx: Context):
    mc = ctx.inject(Mecha)
    mc.spec.parsers["macro_line_variable"] = AlternativeParser(
        [
            InterpolationParser("macro_line_variable"),
            mc.spec.parsers["macro_line_variable"],
        ]
    )

    runtime = ctx.inject(Runtime)
    runtime.helpers["interpolate_macro_line_variable"] = converter(
        AstMacroLineText.from_value
    )


beet_default = macro_interpolation
