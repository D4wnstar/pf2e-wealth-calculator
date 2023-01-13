import pandas as pd
import os

# Global file access
def _pathfinder(path): return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)
# List of all items
itemlist = pd.read_csv(_pathfinder("tables/PF2eItemList.csv"),
                    dtype={'Level': int})
# List of just runes
# TODO: Remove the runelist, superseded by restrict_cat in parse_database
runes = pd.read_csv(_pathfinder('tables/runes.csv'))
# Rune name translation table
rune_replacer = pd.read_csv(_pathfinder('tables/rune_replacer.csv'),
                            names=["name", "replacer"])
# Treasure by level table
tbl = pd.read_csv(_pathfinder('tables/treasurebylevel.csv'))
# Precious materials
with open(_pathfinder('tables/materials.csv')) as _mats:
    materials = _mats.readlines()
    materials = [mat.rstrip("\n") for mat in materials]

# Make all names lowercase
itemlist.columns = itemlist.columns.str.lower()
runes.columns = runes.columns.str.lower()
for col in ["name", "rarity", "category"]:
    itemlist[col] = itemlist[col].apply(lambda name: name.lower())
    runes[col] = runes[col].apply(lambda name: name.lower())

# Fill NaN values with empty strings
rune_replacer["replacer"].fillna("", inplace=True)