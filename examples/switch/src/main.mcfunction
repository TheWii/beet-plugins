from bolt_expressions import Scoreboard

obj = Scoreboard("obj.test")

# switch obj["@s"]:
#     case 1:
#         say one
#         for i in range(3):
#             say i
#     case obj["$a"]:
#         say a

function ./test:
    for i in range(3):
        say i


say a
