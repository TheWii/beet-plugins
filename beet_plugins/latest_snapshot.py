"""Plugin for updating the Mecha command spec to the latest snapshot."""

__all__ = [
    "beet_default",
    "latest_snapshot",
    "nesting",
    "NestedCommandsTransformer",
]

from dataclasses import dataclass, field, replace
from importlib.resources import files
from typing import Generator, List, cast

from beet import Context, Function, configurable
from beet.core.utils import required_field
from mecha import AstChildren, AstCommand, AstResourceLocation, AstRoot, CommandTree, CompilationDatabase, Diagnostic, Mecha, MutatingReducer, rule
from tokenstream import set_location

from mecha.contrib.nesting import InplaceNestingPredicate, NestingOptions
from mecha.contrib.nested_location import NestedLocationResolver


COMMANDS_URL = (
    "https://raw.githubusercontent.com/misode/mcmeta/summary/commands/data.json"
)


def beet_default(ctx: Context):
    ctx.require(latest_snapshot)


def latest_snapshot(ctx: Context):
    """
    Fetches and updates the command tree of the Mecha command spec.

    This plugin should be placed before implicit execute, nested resources or bolt
    on the require list.
    """

    mc = ctx.inject(Mecha)

    path = ctx.cache["latest_commands"].download(COMMANDS_URL)
    mc.spec.add_commands(CommandTree.parse_file(path))

    commands_json = files("beet_plugins.resources").joinpath("latest_snapshot.json").read_text()
    mc.spec.add_commands(CommandTree.parse_raw(commands_json))

    ctx.require(nesting)


@configurable(validator=NestingOptions)
def nesting(ctx: Context, opts: NestingOptions):
    mc  =ctx.inject(Mecha)
    mc.transform.extend(
        NestedCommandsTransformer(
            generate=ctx.generate,
            database=mc.database,
            generate_execute_template=opts.generate_execute,
            nested_location_resolver=ctx.inject(NestedLocationResolver),
            inplace_nesting_predicate=ctx.inject(InplaceNestingPredicate),
        )
    )


@dataclass
class NestedCommandsTransformer(MutatingReducer):
    """Transformer that handles nested commands."""

    generate: Generator = required_field()
    database: CompilationDatabase = required_field()
    generate_execute_template: str = required_field()
    nested_location_resolver: NestedLocationResolver = required_field()
    inplace_nesting_predicate: InplaceNestingPredicate = required_field()
    
    identifier_map: dict[str, str] = field(default_factory=lambda: {
        "function:name:commands": "function:name",
        "function:name:arguments:commands": "function:name:arguments",
        "function:name:with:block:sourcePos:commands": "function:name:with:block:sourcePos",
        "function:name:with:block:sourcePos:path:commands": "function:name:with:block:sourcePos:path",
        "function:name:with:entity:source:commands": "function:name:with:entity:source",
        "function:name:with:entity:source:path:commands": "function:name:with:entity:source:path",
        "function:name:with:storage:source:commands": "function:name:with:storage:source",
        "function:name:with:storage:source:path:commands": "function:name:with:storage:source:path",
        "append:function:name:commands": "function:name",
        "prepend:function:name:commands": "function:name",
    })

    def emit_function(self, path: str, root: AstRoot):
        """Helper method for emitting nested commands into a separate function."""
        function = Function(original=self.database.current.original)
        self.generate(path, function)
        self.database[function] = replace(
            self.database[self.database.current],
            ast=root,
            resource_location=path,
        )
        self.database.enqueue(function, self.database.step + 1)
    
    def convert_command(self, command: AstCommand) -> AstCommand:
        """Converts commands that contain nested commands into their normal form."""

        if command.identifier in self.identifier_map:
            return replace(
                command,
                identifier=self.identifier_map[command.identifier],
                arguments=AstChildren(command.arguments[:-1]),
            )
        return command

    @rule(AstCommand, identifier="execute:run:subcommand")
    def nesting_execute_function(self, node: AstCommand):
        if isinstance(command := node.arguments[0], AstCommand):
            if command.identifier in self.identifier_map:
                self.handle_function(command)
                return replace(node, arguments=AstChildren([self.convert_command(command)]))

        return node

    @rule(AstRoot)
    def nesting(self, node: AstRoot):
        changed = False
        commands: List[AstCommand] = []

        for command in node.commands:
            if command.identifier in self.identifier_map:
                commands.extend(self.handle_function(command, top_level=True))
                changed = True
                continue

            args = command.arguments
            stack: List[AstCommand] = [command]

            expand = None

            while args and isinstance(subcommand := args[-1], AstCommand):
                if subcommand.identifier == "execute:expand:commands":
                    expand = subcommand
                    break
                stack.append(subcommand)
                args = subcommand.arguments

            if expand:
                changed = True
                for nested_command in cast(AstRoot, expand.arguments[0]).commands:
                    if nested_command.identifier == "execute:subcommand":
                        expansion = cast(AstCommand, nested_command.arguments[0])
                    else:
                        expansion = AstCommand(
                            identifier="execute:run:subcommand",
                            arguments=AstChildren([nested_command]),
                        )
                        expansion = set_location(expansion, nested_command)

                    for prefix in reversed(stack):
                        args = AstChildren([*prefix.arguments[:-1], expansion])
                        expansion = replace(prefix, arguments=args)

                    commands.append(expansion)

            else:
                commands.append(command)

        if changed:
            return replace(node, commands=AstChildren(commands))

        return node

    def handle_function(
        self,
        node: AstCommand,
        top_level: bool = False,
    ) -> List[AstCommand]:
        name, *args, root = node.arguments

        if isinstance(name, AstResourceLocation) and isinstance(root, AstRoot):
            path = name.get_canonical_value()

            if top_level:
                if node.identifier in (
                    "function:name:arguments:commands",
                    "function:name:with:block:sourcePos:commands",
                    "function:name:with:block:sourcePos:path:commands",
                    "function:name:with:entity:source:commands",
                    "function:name:with:entity:source:path:commands",
                    "function:name:with:storage:source:commands",
                    "function:name:with:storage:source:path:commands",
                ):
                    d = Diagnostic("error", f"Can't define function with arguments. Use 'execute function ...' instead.")
                    raise set_location(d, node, args[-1])
            else:
                if node.identifier == "append:function:name:commands":
                    d = Diagnostic("error", f"Can't append commands with execute.")
                    raise set_location(d, node, name)
                if node.identifier == "prepend:function:name:commands":
                    d = Diagnostic("error", f"Can't prepend commands with execute.")
                    raise set_location(d, node, name)

            target = self.database.index.get(path)

            if not target:
                self.emit_function(path, root)

            elif node.identifier in (
                "function:name:commands",
                "function:name:arguments:commands",
                "function:name:with:block:sourcePos:commands",
                "function:name:with:block:sourcePos:path:commands",
                "function:name:with:entity:source:commands",
                "function:name:with:entity:source:path:commands",
                "function:name:with:storage:source:commands",
                "function:name:with:storage:source:path:commands",
            ):
                if self.database[target].ast != root:
                    d = Diagnostic(
                        "error",
                        f'Redefinition of function "{path}" doesn\'t match existing implementation.',
                    )
                    raise set_location(d, name)

            elif self.inplace_nesting_predicate.callback(target):
                if node.identifier == "prepend:function:name:commands":
                    d = Diagnostic(
                        "error",
                        f'Can\'t prepend commands to the current function "{path}".',
                    )
                    raise set_location(d, node, name)

                return list(root.commands)

            else:
                compilation_unit = self.database[target]

                if compilation_unit.ast:
                    compilation_unit.ast = replace(
                        compilation_unit.ast,
                        commands=AstChildren(
                            compilation_unit.ast.commands + root.commands
                            if node.identifier == "append:function:name:commands"
                            else root.commands + compilation_unit.ast.commands
                        ),
                    )
                else:
                    compilation_unit.ast = root

            return []

        else:
            return [node]