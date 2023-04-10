
foo = 1b + 1b

_item = {id:"minecraft:diamond", Count: 7b, tag:{Damage:0s,Unbreakable:1b}}

give @s _item.id{**_item.tag} int(_item.Count)

print(127b, Byte(127))