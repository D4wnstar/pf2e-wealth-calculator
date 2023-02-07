import pandas as pd
import os


# Global file access
def _pathfinder(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


# List of all items
itemlist = pd.read_csv(_pathfinder("tables/PF2eItemList.csv"), dtype={"Level": int})
# Rune name translation table
rune_replacer = pd.read_csv(
    _pathfinder("tables/rune_replacer.csv"), names=["name", "replacer"]
)
# Treasure by level table
tbl = pd.read_csv(_pathfinder("tables/treasurebylevel.csv"))
# Precious materials
with open(_pathfinder("tables/materials.csv"), "r") as _mats:
    materials = _mats.readlines()
    materials = [mat.rstrip("\n") for mat in materials]


# Make all names lowercase
itemlist.columns = itemlist.columns.str.lower()
itemlist["subcategory"].fillna("None", inplace=True)
for col in ["name", "rarity", "category", "subcategory"]:
    itemlist[col] = itemlist[col].apply(lambda name: name.lower())

# Replace NaN bulk with zero bulk
itemlist["bulk"].fillna("0", inplace=True)

# Fill NaN values with empty strings
rune_replacer["replacer"].fillna("", inplace=True)
