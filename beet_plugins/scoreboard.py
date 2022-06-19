from dataclasses import dataclass, field
from typing import List
from beet import Context, Function
from beet.core.utils import required_field
from mecha import AstObjective, Mecha, Reducer, rule
from pydantic import BaseModel, Field


def beet_default(ctx: Context):
    manager = ctx.inject(ScoreboardManager)
    yield
    manager.finalize()


class ScoreboardOptions(BaseModel):
    """Scoreboard Options"""

    path: str = "objectives"
    criteria: dict = Field(default_factory=dict)
    ignore: list = Field(default_factory=list)


@dataclass
class ScoreboardManager:
    ctx: Context = required_field(repr=False)
    objectives: List[str] = field(default_factory=list)
    opts: ScoreboardOptions = field(init=False)

    def __post_init__(self):
        self.opts = self.ctx.validate("scoreboard", ScoreboardOptions)
        self.mc = self.ctx.inject(Mecha)
        self.mc.check.extend(ScoreboardChecker(manager=self))
        for name in self.opts.criteria:
            self.add_objective(name)

    def get_criteria(self, objective: str):
        return self.opts.criteria.get(objective, "dummy")

    def add_objective(self, name: str, criteria=None):
        if not name in self.objectives and not name in self.opts.ignore:
            self.objectives.append(name)
        if criteria:
            self.opts.criteria[name] = criteria

    def finalize(self):
        self.ctx.generate(
            self.opts.path,
            Function(
                [
                    f"scoreboard objectives add {objective} {self.get_criteria(objective)}"
                    for objective in self.objectives
                ],
                prepend_tags=["minecraft:load"],
            ),
        )


@dataclass
class ScoreboardChecker(Reducer):
    manager: ScoreboardManager = required_field()

    @rule(AstObjective)
    def objective(self, node: AstObjective):
        self.manager.add_objective(node.value)
