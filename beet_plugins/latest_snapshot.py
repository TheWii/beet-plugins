"""Plugin for updating the Mecha command spec to the latest snapshot."""

__all__ = [
    "Atlas",
    "beet_default",
    "latest_snapshot",
]

from contextlib import suppress
from copy import deepcopy
from typing import ClassVar, Tuple

from beet import Context, JsonFile
from beet.core.utils import JsonDict
from mecha import CommandTree, Mecha, delegate

COMMANDS_URL = (
    "https://raw.githubusercontent.com/misode/mcmeta/summary/commands/data.json"
)


class Atlas(JsonFile):
    """Class representing an atlas configuration file."""

    scope: ClassVar[Tuple[str, ...]] = ("atlases",)
    extension: ClassVar[str] = ".json"

    def merge(self, other: "Atlas") -> bool:  # type: ignore
        values = self.data.setdefault("sources", [])

        for value in other.data.get("sources", []):
            if value not in values:
                values.append(deepcopy(value))
        return True

    def append(self, other: "Atlas"):
        """Append values from another atlas."""

        self.merge(other)

    def prepend(self, other: "Atlas"):
        """Prepend values from another atlas."""

        values = self.data.setdefault("sources", [])

        for value in other.data.get("sources", []):
            if value not in values:
                values.insert(0, deepcopy(value))

    def add(self, value: str):
        """Add an entry."""

        values = self.data.setdefault("sources", [])
        if value not in values:
            values.append(value)

    def remove(self, value: str):
        """Remove an entry."""

        values = self.data.setdefault("sources", [])
        with suppress(ValueError):
            values.remove(value)

    @classmethod
    def default(cls) -> JsonDict:
        return {"sources": []}


def beet_default(ctx: Context):
    ctx.require(latest_snapshot)


def latest_snapshot(ctx: Context):
    """
    Fetches and updates the command tree of the Mecha command spec.

    This plugin should be placed before implicit execute, nested resources or bolt
    on the require list.
    """

    mc = ctx.inject(Mecha)

    ctx.assets.extend_namespace += [Atlas]

    path = ctx.cache["latest_commands"].download(COMMANDS_URL)
    mc.spec.add_commands(CommandTree.parse_file(path))

    mc.spec.parsers["command:argument:minecraft:gamemode"] = delegate("gamemode")
