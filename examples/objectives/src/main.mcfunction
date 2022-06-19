scoreboard players add $temp obj.value 1
scoreboard players operation $a math.abc = $b math.temp
execute if score @s kills matches 1..
tag @s[scores={abcdefg=1..}] remove foo

scoreboard players enable @a obj.settings


# directly add an objective using the api
from beet_plugins.scoreboard import ScoreboardManager

score_manager = ctx.inject(ScoreboardManager)

score_manager.add_objective("another.obj")
score_manager.add_objective("another.settings", "trigger")