atlas ./test {
    "sources": [
        {
            "type": "directory",
            "source": "assembly",
            "prefix": "assembly/"
        }
    ]
}

on vehicle at @s
    if loaded ~10 ~ ~
    tp @s ~10 ~ ~
execute on vehicle at @s
    if loaded ~10 ~ ~
    tp @s ~10 ~ ~

execute if biome ~10 ~ ~ minecraft:plains say .
execute if dimension minecraft:overworld run say .
execute unless loaded ~ ~ ~ say .
execute unless biome ~10 ~ ~ minecraft:forest say .
execute unless dimension minecraft:overworld say .
if biome ~10 ~ ~ minecraft:plains say .
if dimension minecraft:overworld run say .
unless loaded ~ ~ ~ say .
unless biome ~10 ~ ~ minecraft:forest say .
unless dimension minecraft:overworld say .

fillbiome ~ ~ ~ ~16 ~16 ~16 minecraft:deep_dark

gamemode survival @a

gamerule blockExplosionDropDecay true
gamerule commandModificationBlockLimit 1000
gamerule globalSoundEvents false
gamerule lavaSourceConversion true
gamerule mobExplosionDropDecay true
gamerule snowAccumulationHeight 10
gamerule tntExplosionDropDecay true
gamerule waterSourceConversion true

clone ~ ~ ~ ~10 ~10 ~10 0 0 0 masked
clone from overworld ~ ~ ~ ~10 ~10 ~10 0 0 0 masked
clone ~ ~ ~ ~10 ~10 ~10 to nether 0 0 0 masked
clone from overworld ~ ~ ~ ~10 ~10 ~10 to nether 0 0 0 masked

data modify block ~ ~ ~ Name set string storage test:main value 0 1
data modify block ~ ~ ~ Name append string block ~ ~1 ~ value 0 1
data modify block ~ ~ ~ Name prepend string entity @s EntityName 0 1
data modify block ~ ~ ~ Name insert 0 string storage test:main value 0 1
data modify block ~ ~ ~ Name merge string storage test:main value 0 1

title @s times 0.5s 10t 1d

weather clear 10t
weather rain 0.235s
weather thunder 1d

ride @s mount @e[type=pig,limit=1,sort=nearest]
ride @s dismount

if score @s abc matches 0 ride @s dismount