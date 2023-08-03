
if function ./test function ./foo {arg:123}

return run function ./a

say calling function with parameters
function ./bar0 {i:10}
function ./bar1 with entity @s
function ./bar2 with entity @s Inventory
function ./bar3 with storage ./temp
function ./bar4 with storage ./temp args
function ./bar5 with block ~ ~ ~
function ./bar6 with block ~ ~ ~ Items
function ./bar7 with storage ./temp
function ./bar8 with storage ./temp args

say it's forbidden to define and call function with parameters
say error: Can't define function with arguments. Use 'execute function ...' instead.
# function ./bar0 {i:10}:
#     say nested definition!
# function ./bar1 with entity @s:
#     say nested definition!
# function ./bar2 with entity @s Inventory:
#     say nested definition!
# function ./bar3 with storage ./temp:
#     say nested definition!
# function ./bar4 with storage ./temp args:
#     say nested definition!
# function ./bar5 with block ~ ~ ~:
#     say nested definition!
# function ./bar6 with block ~ ~ ~ Items:
#     say nested definition!
# function ./bar7 with storage ./temp:
#     say nested definition!
# function ./bar8 with storage ./temp args:
#     say nested definition!

say define and execute function with parameters
execute function ./bar0 {i:10}:
    say nested definition!
execute function ./bar1 with entity @s:
    say nested definition!
execute function ./bar2 with entity @s Inventory:
    say nested definition!
execute function ./bar3 with storage ./temp:
    say nested definition!
execute function ./bar4 with storage ./temp args:
    say nested definition!
execute function ./bar5 with block ~ ~ ~:
    say nested definition!
execute function ./bar6 with block ~ ~ ~ Items:
    say nested definition!
execute function ./bar7 with storage ./temp:
    say nested definition!
execute function ./bar8 with storage ./temp args:
    say nested definition!


# just checking if i havent broken the nesting plugin :)
if function ./test expand:
    say a
    say b
if function ./test:
    say a
    say b

append function ./bar9:
    say appended!

prepend function ./bar9:
    say prepended!



from bolt_expressions import Data

strg = Data.storage(./temp)

execute function ./test with var strg.args:
    say .