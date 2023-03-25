from pf2e_wealth_calculator.dataframes import itemlist, rune_replacer, tbl, materials
from pf2e_wealth_calculator.structs import *

import pandas as pd
import numpy as np
from tabulate import tabulate

import re
from difflib import get_close_matches

import sys
import textwrap
import typing  # for backwards compatibility to python 3.9


def get_higher_rarity(rar1: str, rar2: str) -> str:
    """Get the higher rarity among the two given ones."""

    ordering = {"common": 1, "uncommon": 2, "rare": 3}

    rarnum1 = ordering[rar1]
    rarnum2 = ordering[rar2]

    return rar1 if rarnum1 > rarnum2 else rar2


def get_material_grade(
    name_split: list[str], materials: list[str] = materials
) -> tuple[str, typing.Union[str, None], typing.Union[str, None]]:
    """Get the grade and material from an item's name, if present."""

    if name_split[0] in materials:
        material = name_split.pop(0)
    elif len(name_split) > 1 and f"{name_split[0]} {name_split[1]}" in materials:
        # Both pops are zero because they happen in sequence
        # so the first one pops element zero and the second
        # pops element one
        material = f"{name_split.pop(0)} {name_split.pop(0)}"
    else:
        return " ".join(name_split), None, None

    grade = name_split.pop(-1)

    if "low" in grade:
        grade = "(low-grade)"
    elif "standard" in grade:
        grade = "(standard-grade)"
    elif "high" in grade:
        grade = "(high-grade)"

    base_name = " ".join(name_split)

    # There is no entry for "shield" so it defaults to "steel shield",
    # unless it's a darkwood shield, in which case it must be a "wooden shield"
    if base_name == "shield" and material == "darkwood":
        base_name = "wooden shield"
    elif base_name == "shield":
        base_name = "steel shield"

    return base_name, material, grade


def parse_database(
    item_name: str,
    amount: int,
    *,
    restrict_cat: typing.Union[str, None] = None,
    df: pd.DataFrame = itemlist,
    materials: list[str] = materials,
    quiet: bool = False,
) -> ItemInfo:
    """Parses the Archives of Nethys item list and returns information about the item."""

    item_name = item_name.strip()

    # Check if the item name is just plain currency, in which case exit early
    # The regex checks for an asterisk maybe followed by spaces, then digits, then an optional decimal
    # comma or dot followed by more digits, followed by cp, sp or gp after any amount of spaces
    if re.match(r"\*?\ *\d+([,\.]\d*)?\ *(cp|sp|gp)", item_name) is not None:
        if item_name.find("*") == 0:
            item_name = item_name.replace("*", "", 1)
            currency_value = get_price(item_name, amount, origin=Origins.ART_OBJECT)
            return ItemInfo(item_name, currency_value, "art objects", "none")
        else:
            currency_value = get_price(item_name, amount, origin=Origins.CURRENCY)
            return ItemInfo(item_name, currency_value, "currency", "none")

    # Check if the first one or two words denote a precious material
    item_name, material, grade = get_material_grade(item_name.split(), materials)

    # Special case for handwraps which don't have a real listing
    # They're technically "worn items", not "weapons", but using the right category
    # breaks potency rune price calculation
    if item_name == "handwraps of mighty blows":
        return ItemInfo(
            "handwraps of mighty blows",
            category="weapons",
            subcategory="other worn items",
        )

    # If category is restricted, check only items from that category
    # TODO: This can probably be simplified
    if restrict_cat:
        filtered_list = itemlist.set_index("category")
        filtered_list = filtered_list.filter(like=restrict_cat, axis=0)
        item_row = filtered_list[filtered_list["name"] == item_name]
    else:
        item_row = df[df["name"] == item_name]

    # If there is no item with the given name, find closest item to suggest
    # and print a warning
    if item_row.empty:
        if not quiet:
            suggestion = "".join(
                get_close_matches(item_name.strip(), df["name"].tolist(), 1, 0)
            )

            if item_name != suggestion:
                print(
                    f'WARNING: Ignoring item "{item_name}". Did you mean "{suggestion}"?'
                )

        return ItemInfo(item_name, category="error")

    # Fix shield name including "steel" or "wooden" even if it's made of a precious material
    if material and "shield" in item_name and not "tower" in item_name:
        item_name = "shield"

    # Get item stats
    item_category = item_row["category"].item() if not restrict_cat else restrict_cat
    item_subcategory = item_row["subcategory"].item()
    item_level = item_row["level"].item()
    item_rarity = item_row["rarity"].item()
    item_bulk = item_row["bulk"].item()
    if item_bulk.isdigit():
        item_bulk = int(item_bulk)

    # Get item price
    if not material:
        item_price = get_price(item_row["price"].item(), amount)
    else:
        item_name = f"{material} {item_name} {grade}"
        # Convert category to a AoN-legible name
        categories = {
            "weapons": "weapon",
            "armor": "armor",
            "shields": "shield",
        }

        if "buckler" in item_name:
            # Bucklers are priced differently than other shields
            category = "buckler"
        elif item_category in categories.keys():
            category = categories[item_category]
        else:
            # If it's not a weapon, an armor set or a shield, it's a generic object
            category = "object"

        material_name = f"{material} {category} {grade}"
        material_row = df[df["name"] == material_name]

        # Add the price of the precious material
        item_price = get_price(material_row["price"].item(), amount)
        # Add the extra price based on bulk
        # Formula: price of precious item + 10% of price * Bulk (for weapons and armor)
        #          price of precious item * Bulk (for objects)
        #          No additions for shields and bucklers
        if type(item_bulk) is int and category in ("weapon", "armor"):
            item_price.gp += item_price.gp // 10 * item_bulk
        elif category == "object":
            multiplier = (
                1 if type(item_bulk) is str and "L" in item_bulk else int(item_bulk)
            )
            item_price = item_price * multiplier if multiplier > 0 else item_price

        # Materials have their own level and rarity, pick the highest ones
        material_level = material_row["level"].item()
        item_level = material_level if material_level > item_level else item_level

        material_rarity = material_row["rarity"].item()
        item_rarity = get_higher_rarity(material_rarity, item_rarity)

    return ItemInfo(
        item_name,
        item_price,
        item_category,
        item_subcategory,
        item_level,
        item_rarity,
        item_bulk,
    )


def get_potency_rune_stats(
    cached_rune: str, category: typing.Union[str, None], level: int
) -> tuple[Money, int]:
    "Use the cached potency rune to add the appropriate price, depending on category"

    if category == "weapons":
        if cached_rune == "+1":
            level = 2 if 2 > level else level
            return Money(0, 0, 35), level
        elif cached_rune == "+2":
            level = 10 if 10 > level else level
            return Money(0, 0, 935), level
        elif cached_rune == "+3":
            level = 16 if 16 > level else level
            return Money(0, 0, 8935), level
        else:
            raise ValueError("Invalid potency rune.")

    elif category == "armor":
        if cached_rune == "+1":
            level = 5 if 5 > level else level
            return Money(0, 0, 160), level
        elif cached_rune == "+2":
            level = 11 if 11 > level else level
            return Money(0, 0, 1060), level
        elif cached_rune == "+3":
            level = 18 if 18 > level else level
            return Money(0, 0, 20560), level
        else:
            raise ValueError("Invalid potency rune.")

    else:
        return Money(), level


def check_multiword_item(item, amount, item_runes, cur_index):
    item += " " + " ".join(item_runes[cur_index + 1 :])
    item_info = parse_database(item, amount, quiet=True)
    if item_info.category != "error":
        return item_info
    else:
        return ItemInfo(item, category="error")


def rune_calculator(
    item_name,
    amount,
    df: pd.DataFrame = itemlist,
    rune_names: pd.DataFrame = rune_replacer,
    materials: list[str] = materials,
) -> ItemInfo:
    """Automatically breaks down the item's name into singular runes and calculates price for each."""

    running_sum = Money()
    rune_info = ItemInfo()
    highest_level = 0
    highest_rarity = "common"
    potency_rune = "0"
    skip_cycle = False
    material_flag = False

    item_runes = item_name.split()  # Break up the name into single runes

    # Cycle through runes found in the item name
    for cur_index, rune in enumerate(item_runes):
        if skip_cycle:
            skip_cycle = False
            continue

        rune = rune.strip()

        # Find potency rune and cache it
        if rune == "+1":
            potency_rune = "+1"
            continue
        elif rune == "+2":
            potency_rune = "+2"
            continue
        elif rune == "+3":
            potency_rune = "+3"
            continue

        # If rune is a prefix, fuse it with the next one, short-circuit, and skip next cycle
        if rune in ("lesser", "moderate", "greater", "major", "true"):
            rune = f"{item_runes[cur_index + 1]} ({rune})"
            rune_info = parse_database(rune, amount, quiet=True)
            running_sum += rune_info.price
            highest_level = (
                rune_info.level if rune_info.level > highest_level else highest_level
            )
            highest_rarity = get_higher_rarity(highest_rarity, rune_info.rarity)
            skip_cycle = True
            continue

        # Replace the name if necessary. If it is replaced, short-circuit
        rune_row = rune_names[rune_names["name"] == rune]
        if not rune_row.empty and len(rune_row["replacer"].item()) > 0:
            rune_info = parse_database(rune_row["replacer"].item(), amount, quiet=True)
            running_sum += rune_info.price
            highest_level = (
                rune_info.level if rune_info.level > highest_level else highest_level
            )
            highest_rarity = get_higher_rarity(highest_rarity, rune_info.rarity)
            skip_cycle = True
            continue
        elif not rune_row.empty and len(rune_row["replacer"].item()) == 0:
            continue

        # Find the rune in the list of runes (if present)
        if rune not in materials:
            rune_info = parse_database(rune, amount, restrict_cat="runes")
        else:
            rune_info = ItemInfo(rune, category="error")
            material_flag = True

        # If it's not a rune, use the remainder of the name to find the correct base item
        if rune_info.category == "error":
            rune_info = check_multiword_item(rune, amount, item_runes, cur_index)
            if rune_info.category != "error":
                highest_level = (
                    rune_info.level
                    if rune_info.level > highest_level
                    else highest_level
                )
                highest_rarity = get_higher_rarity(highest_rarity, rune_info.rarity)
                running_sum += rune_info.price
                break
            else:
                print(
                    f"WARNING: No results for {item_name}. Skipping price calculation."
                )
                return ItemInfo(item_name, category="error")
        else:
            highest_level = (
                rune_info.level if rune_info.level > highest_level else highest_level
            )
            highest_rarity = get_higher_rarity(highest_rarity, rune_info.rarity)

        # Add rune/base item price to the total
        running_sum += rune_info.price

    # Manually change the grade tag into the standardized form
    if material_flag:
        for grade in ("low", "standard", "high"):
            if grade in item_runes[-1]:
                item_runes[-1] = f"({grade}-grade)"
                item_name = " ".join(item_runes)
                break

    # Add potency rune price
    add_to_sum, highest_level = get_potency_rune_stats(
        potency_rune, rune_info.category, highest_level
    )
    running_sum += add_to_sum
    return ItemInfo(
        item_name,
        running_sum,
        rune_info.category,
        rune_info.subcategory,
        highest_level,
        highest_rarity,
        rune_info.bulk,
    )


def get_price(price_str: str, amount: int = 1, origin: Origins = Origins.ITEM) -> Money:
    """
    Get the price of the given item.

    price_str is a string that includes the price and coin type (i.e. "12 gp").
    """

    # Fetch price and coin type through regex
    try:
        price_match = re.search(r"\d*(,\d*)?", price_str)
        type_match = re.search(r"cp|sp|gp", price_str)
    except TypeError:
        return Money()

    # Check which kind of coin it is (if any)
    if type_match is not None and price_match is not None:
        # Add to total while multiplying by quantity
        item_price = price_match.group()
        coin_type = type_match.group()

        if coin_type == "cp":
            return Money(int(item_price.replace(",", "")) * amount, 0, 0, origin=origin)
        elif coin_type == "sp":
            return Money(0, int(item_price.replace(",", "")) * amount, 0, origin=origin)
        elif coin_type == "gp":
            return Money(0, 0, int(item_price.replace(",", "")) * amount, origin=origin)
        else:  # This shouldn't even be reachable
            raise ValueError("Invalid currency type")
    else:
        return Money()


def process_loot_file(filepath: str) -> pd.DataFrame:
    # User-defined loot
    loot = pd.read_csv(filepath, names=["name", "amount"])
    # Skip rows starting in #
    # TODO: Skip only if # is the first character
    for i, row in enumerate(loot["name"]):
        if "#" in row:
            loot.drop(i, axis=0, inplace=True)

    loot["name"] = loot["name"].apply(lambda name: name.lower())
    # Assume no amount means 1
    loot["amount"].fillna(1, inplace=True)
    # Uses regex to replace non-numeric values in the "Amount" column
    loot["amount"].replace(r"\D", 0, regex=True, inplace=True)
    loot["amount"] = loot["amount"].astype(int)

    return loot


def get_loot_stats(
    loot: pd.DataFrame,
    money: dict[Origins, Money],
    levels: dict[str, int],
    categories: dict[str, int],
    subcategories: dict[str, int],
    rarities: dict[str, int],
):
    """Get the price for each item in the loot DataFrame."""
    for _, row in loot.iterrows():
        name, amount = row.tolist()
        # Check if there is a fundamental rune in the item
        if "+1" in name or "+2" in name or "+3" in name:
            curr_item = rune_calculator(name, amount)
        else:
            curr_item = parse_database(name, amount)

        money[curr_item.price.origin] += curr_item.price

        try:
            levels[str(curr_item.level)] += amount
        except KeyError:
            levels[str(curr_item.level)] = amount

        try:
            categories[curr_item.category] += amount
        except KeyError:
            categories[curr_item.category] = amount

        try:
            subcategories[curr_item.subcategory] += amount
        except KeyError:
            subcategories[curr_item.subcategory] = amount

        try:
            rarities[curr_item.rarity] += amount
        except KeyError:
            rarities[curr_item.rarity] = amount


def convert_input_level(level) -> typing.Union[int, tuple[int, int]]:
    """Transform the user input level into a integer or a tuple of two integers."""
    try:
        level = [int(x) for x in level.split("-")]
    except ValueError:
        print(
            "Invalid level type\nPlease only insert an integer or a range with the syntax X-Y"
        )
        sys.exit(1)

    if len(level) == 1:
        level = level[0]
    elif len(level) == 2:
        level = tuple(level)
    else:
        print(
            "Invalid level type\nPlease only insert an integer or a range with the syntax X-Y"
        )
        sys.exit(1)

    return level


def get_value_from_level(level) -> int:
    """Find the amount of gold expected by the Treasure by Level table for the range of levels provided."""
    if type(level) is tuple:
        if 0 < level[0] <= 20 and 0 < level[1] <= 20:
            total_value = tbl["Total Value"][min(level) - 1 : max(level)].sum()
        else:
            print("Please only insert levels between 1 and 20")
            sys.exit(1)

    elif type(level) is int:
        if 0 < level <= 20:
            total_value = tbl.at[level - 1, "Total Value"]
        else:
            print("Please only insert a level between 1 and 20")
            sys.exit(1)

    else:
        print(
            "Invalid level type\nPlease only insert an integer or a range with the syntax X-Y"
        )
        sys.exit(1)  # Probably unreachable, but type safety y'know

    return total_value


def console_entry_point(
    input_files: list[str],
    level_str: str,
    currency: int,
    detailed: bool,
    noconversion: bool,
):
    """Primary entry point for the script."""

    money = {
        Origins.ITEM: Money(origin=Origins.ITEM),
        Origins.ART_OBJECT: Money(origin=Origins.ART_OBJECT),
        Origins.CURRENCY: Money(origin=Origins.CURRENCY),
    }
    levels: dict[str, int] = {}
    categories: dict[str, int] = {}
    subcategories: dict[str, int] = {}
    rarities: dict[str, int] = {}

    for file in input_files:
        loot = process_loot_file(file)

        get_loot_stats(loot, money, levels, categories, subcategories, rarities)

        if level_str:
            level = convert_input_level(level_str)
            total_value = get_value_from_level(level)

    money[Origins.CURRENCY] += Money(gp=currency, origin=Origins.CURRENCY)

    # Convert coins in gp where possible, if requested
    if not noconversion:
        for origin in money.keys():
            money[origin].gp += money[origin].cp // 100
            money[origin].gp += money[origin].sp // 10
            money[origin].cp %= 100
            money[origin].sp %= 10

    def get_total(money_list):
        res = Money(origin=Origins.TOTAL, check_origin=False)
        for item in money_list:
            res += item
        return res

    money[Origins.TOTAL] = get_total(money.values())

    print("\nTotal value", end="")
    if not noconversion:
        print(" (converted in gp)", end="")
    print(":")
    print(
        textwrap.dedent(
            f"""\
          - {money[Origins.TOTAL].cp} cp
          - {money[Origins.TOTAL].sp} sp
          - {money[Origins.TOTAL].gp} gp

        Of which:
          - Items: {money[Origins.ITEM].gp} gp
          - Art objects: {money[Origins.ART_OBJECT].gp} gp
          - Currency: {money[Origins.CURRENCY].gp} gp\
        """
        )
    )

    if level:
        print("\nDifference:")
        if total_value - money[Origins.TOTAL].gp < 0:
            print(
                f"  - {abs(total_value - money[Origins.TOTAL].gp)} gp too much (Expected {total_value} gp)"
            )
        elif total_value - money[Origins.TOTAL].gp > 0:
            print(
                f"  - {abs(total_value - money[Origins.TOTAL].gp)} gp too little (Expected {total_value} gp)"
            )
        else:
            print(f"  - None (Expected {total_value} gp)")

    if detailed:
        print("\nLevels:")
        for lvl, amount in levels.items():
            print(f"  - Level {lvl}: {amount}")

        print("\nCategories:")
        for cat, amount in categories.items():
            print(f"  - {cat.capitalize()}: {amount}")

        print("\nSubcategories:")
        for subcat, amount in subcategories.items():
            print(f"  - {subcat.capitalize()}: {amount}")

        print("\nRarities:")
        for rar, amount in rarities.items():
            print(f"  - {rar.capitalize()}: {amount}")

    print()


def find_single_item(item_name: str):
    """Fetches and prints information on a single item instead of a table."""

    item_name = item_name.lower()

    if "+1" in item_name or "+2" in item_name or "+3" in item_name:
        item = rune_calculator(item_name, 1)
    else:
        item = parse_database(item_name, 1)

    if item.price.gp != 0:
        print(f"Value: {item.price.gp}gp")
    elif item.price.sp != 0:
        print(f"Value: {item.price.sp}sp")
    elif item.price.cp != 0:
        print(f"Value: {item.price.cp}cp")
    else:
        print("Value: Undefined")

    print(
        textwrap.dedent(
            f"""\
        Level: {item.level}
        Category: {item.category.capitalize()}
        Subcategory: {item.subcategory.capitalize()}
        Rarity: {item.rarity.capitalize()}
        Bulk: {item.bulk}\
        """
        )
    )


def generate_random_items(n_of_items: int, level_str: str = "0-100"):
    level = convert_input_level(level_str)

    if type(level) is int:
        rand_ids = np.random.choice(
            itemlist[itemlist["level"] == level].index, n_of_items
        )
        rand_items = itemlist.iloc[rand_ids]
    elif type(level) is tuple:
        rand_ids = np.random.choice(
            itemlist[
                (itemlist["level"] >= level[0]) & (itemlist["level"] <= level[1])
            ].index,
            n_of_items,
        )
        rand_items = itemlist.iloc[rand_ids]
    else:
        sys.exit(1)

    rand_items = rand_items.applymap(lambda word : word.capitalize() if type(word) is str else word)

    print()
    print(
        tabulate(
            rand_items, # type: ignore
            headers=rand_items.columns.str.capitalize(), # type: ignore
            showindex=False,
            tablefmt="rounded_outline"
        )
    )
    print()