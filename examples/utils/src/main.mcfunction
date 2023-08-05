from utils:data import loop
from bolt_expressions import Data

strg = Data.storage(./temp)

with loop(strg.items) as element:
    tellraw @a element.id