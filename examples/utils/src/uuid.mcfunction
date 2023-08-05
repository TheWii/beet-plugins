
from bolt_expressions import Scoreboard, Data
from json import dumps

from utils:uuid import uuid_array_to_hex, as_uuid
from utils:db import StorageDB
from utils:objectives import temp_obj, temp_data


this = Data.entity("@s")
ids = Scoreboard("obj.ids", "dummy")

db_main = StorageDB((./db, "main"), ./database/main)
db_ids = StorageDB((./db, "ids"), ./database/ids)

function ./create:
    temp_data.uuid = this.UUID

    unless score @s ids matches -2147483648.. function ~/id:
        with db_ids.open(temp_data.uuid, create=True) as entry:
            unless data var entry.id function ~/../set_entry_id:
                ids["$id"] += 1
                entry.id = ids["$id"]
            ids["@s"] = entry.id
        del entry
    
    hex_uuid = uuid_array_to_hex(temp_data.uuid)
    with db_main.open(ids["@s"], create=True) as entry:
        entry.uuid = hex_uuid
    del entry


function ./at_id:
    raw f"$scoreboard players set $id {temp_obj} $(id)"

    with db_main.open(temp_obj["$id"], save=False) as entry:
        with as_uuid(entry):
            at @s particle flame ~ ~ ~ 0 0 0 0.1 10 force