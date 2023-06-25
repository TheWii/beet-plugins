from ~/bar import message
print(message)

path = ~/other
#from path import msg
# ModuleNotFoundError: No module named 'path'

print(~/)

print(~/abc)
print(./abc)

name = ~/abc
function name:
    say hi

function ./relative:
    say hello


print(~/value)
function ~/value:
    say value

with ctx.generate["path/to"].push():
    print(~/value)
    function ~/value:
        say nested value


function_tag minecraft:tick {
    "values": [
        (~/main)
    ]
}

bar = 10
print(~/{bar}/bar)