from beet import Context
from beet.contrib.load import load


def beet_default(ctx: Context):
    ctx.require(
        load(
            data_pack={
                "data/utils/modules": "@beet_plugins/utils",
            },
        ),
    )
