from pf2e_wealth_calculator.dataframes import itemlist, rune_replacer, tbl, materials

import pandas as pd
import re
from difflib import get_close_matches
from dataclasses import dataclass

import sys
import os
import argparse
import textwrap


@dataclass
class Money:
    """Simple data structure for cp/sp/gp amounts."""

    cp: int = 0
    sp: int = 0
    gp: int = 0
    origin: str = "item"
    check_origin: bool = True

    def __add__(self, val):
        if type(val) == int:
            return Money(
                self.cp + val,
                self.sp + val,
                self.gp + val,
                self.origin,
                self.check_origin,
            )

        if type(val) == Money:
            if self.check_origin and val.check_origin and self.origin != val.origin:
                raise ValueError("Origins don't match")
            return Money(
                self.cp + val.cp,
                self.sp + val.sp,
                self.gp + val.gp,
                self.origin,
                self.check_origin,
            )

        raise TypeError(
            f"Unsupported sum operation for type {type(val)} on class Money"
        )

    def __radd__(self, val):
        return self.__add__(val)


@dataclass(frozen=True)
class ItemInfo:
    """Data structure that contains information on a given item."""

    name: str = "item"
    price: Money = Money()
    category: str | None = None
    level: int = 0
    rarity: str = "common"


def get_higher_rarity(rar1: str, rar2: str) -> str:
    """Get the higher rarity among the two given ones."""

    ordering = {"common": 1, "uncommon": 2, "rare": 3}

    rarnum1 = ordering[rar1]
    rarnum2 = ordering[rar2]

    return rar1 if rarnum1 > rarnum2 else rar2


def get_material_grade(
    name_split: list[str], materials: list[str] = materials
) -> tuple[str, str | None, str | None]:
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
    restrict_cat: str | None = None,
    df: pd.DataFrame = itemlist,
    materials: list[str] = materials,
    quiet: bool = False,
) -> ItemInfo:
    """Parses the Archives of Nethys item list and returns information about the item."""

    is_currency = get_price(item_name, amount)
    item_name = item_name.strip()

    # Check if it's plain currency, in which case short-circuit
    if is_currency != Money():
        is_currency.origin = "currency"
        return ItemInfo(item_name, is_currency, "currency")

    # Check if the first one or two words denote a precious material
    item_name, material, grade = get_material_grade(item_name.split(), materials)

    # Special case for handwraps which don't have a real listing
    # They're technically "worn items", not "weapons", but using the right category
    # breaks potency rune price calculation
    if item_name == "handwraps of mighty blows":
        return ItemInfo("handwraps of mighty blows", category="weapons")

    # If category is restricted, check only items from that category
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
            print(f'WARNING: Ignoring item "{item_name}". Did you mean "{suggestion}"?')

        return ItemInfo(item_name, category="error")

    # Fix shield name including "steel" or "wooden" even if it's made of a precious material
    if "shield" in item_name and not "tower" in item_name and material:
        item_name = "shield"

    # Get item stats
    item_category = item_row["category"].item() if not restrict_cat else restrict_cat
    item_level = item_row["level"].item()
    item_rarity = item_row["rarity"].item()

    # Get item price
    if not material:
        item_price = get_price(item_row["price"].item(), amount)
    else:
        item_name = f"{material} {item_name} {grade}"
        # Convert category to a code-legible string
        categories = {
            "weapons": "weapon",
            "armor": "armor",
            "shields": "shield",
            "materials": "object",
            "adventuring gear": "object"
            # TODO: Might need to add more
        }
        category = (
            categories[item_category] if "buckler" not in item_name else "buckler"
        )
        material_name = f"{material} {category} {grade}"

        # Add the price of the precious material
        item_price = get_price(df[df["name"] == material_name]["price"].item(), amount)

        # Materials have their own level and rarity, pick the highest ones
        material_level = df[df["name"] == material_name]["level"].item()
        item_level = material_level if material_level > item_level else item_level

        material_rarity = df[df["name"] == material_name]["rarity"].item()
        item_rarity = get_higher_rarity(material_rarity, item_rarity)

    return ItemInfo(item_name, item_price, item_category, item_level, item_rarity)


def get_potency_rune_stats(
    cached_rune: str, category: str | None, level: int
) -> tuple[Money, int]:
    "Use the cached potency rune to add the appropriate price, depending on category"

    if category == "weapons":
        match cached_rune:
            case "+1":
                level = 2 if 2 > level else level
                return Money(0, 0, 35), level
            case "+2":
                level = 10 if 10 > level else level
                return Money(0, 0, 935), level
            case "+3":
                level = 16 if 16 > level else level
                return Money(0, 0, 8935), level
            case _:
                raise ValueError("Invalid potency rune.")

    elif category == "armor":
        match cached_rune:
            case "+1":
                level = 5 if 5 > level else level
                return Money(0, 0, 160), level
            case "+2":
                level = 11 if 11 > level else level
                return Money(0, 0, 1060), level
            case "+3":
                level = 18 if 18 > level else level
                return Money(0, 0, 20560), level
            case _:
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
    """Automatically breaks down the item's name into singular runes and returns the total price as a Money object."""

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
            rune_info = parse_database(
                rune,
                amount,
                df=df,
                materials=materials,
                restrict_cat="runes",
                quiet=True,
            )
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
        item_name, running_sum, rune_info.category, highest_level, highest_rarity
    )


def get_price(price_str: str, amount: int) -> Money:
    """
    Get the price of the given item.

    price_str is a string that includes the price and coin type (i.e. "12 gp").

    amount is an integer that multiplies the price of the given item before adding it.
    """

    # Fetch price and coin type through regex
    item_match = re.search(r"\d*(,\d*)?", price_str)
    coin_match = re.search(r"cp|sp|gp", price_str)

    # Check which kind of coin it is (if any)
    if coin_match is not None and item_match is not None:
        # Add to total while multiplying by quantity
        item_price = item_match.group()
        coin_type = coin_match.group()

        match coin_type:
            case "cp":
                return Money(int(item_price.replace(",", "")) * amount, 0, 0)
            case "sp":
                return Money(0, int(item_price.replace(",", "")) * amount, 0)
            case "gp":
                return Money(0, 0, int(item_price.replace(",", "")) * amount)
            # This shouldn't even be reachable
            case _:
                raise ValueError("Invalid currency type")
    else:
        return Money()


def console_entry_point(input_file, level, currency, noconversion):
    # User-defined loot
    loot = pd.read_csv(input_file, names=["name", "amount"])
    loot["name"] = loot["name"].apply(lambda name: name.lower())
    # Assume no amount means 1
    loot["amount"].fillna(1, inplace=True)
    # Uses regex to replace non-numeric values in the "Amount" column
    loot["amount"].replace(r"\D", 0, regex=True, inplace=True)
    loot["amount"] = loot["amount"].astype(int)

    money = {"item": Money(origin="item"), "currency": Money(origin="currency")}

    levels: dict[str, int] = {}
    categories: dict[str | None, int] = {}
    rarities: dict[str, int] = {}

    # Get the price for each item
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
            rarities[curr_item.rarity] += amount
        except KeyError:
            rarities[curr_item.rarity] = amount

    # Manage the level, if given
    if level:
        try:
            level = [int(x) for x in level.split("-")]
        except ValueError:
            print(
                "Invalid level type\nPlease only insert an integer or a range with the syntax X-Y"
            )
            sys.exit(1)

        if len(level) == 1:
            level = level[0]
        elif len(level) > 2:
            print(
                "Invalid level type\nPlease only insert an integer or a range with the syntax X-Y"
            )
            sys.exit(1)

        if type(level) is list:
            if 0 < level[0] <= 20 and 0 < level[1] <= 20:
                # Get total value from the TBL table
                total_value = tbl["Total Value"][min(level) - 1 : max(level)].sum()
            else:
                print("Please only insert levels between 1 and 20")
                sys.exit(1)
        elif type(level) is int:
            if 0 < level <= 20:
                # Get total value from the TBL table
                total_value = tbl.at[level - 1, "Total Value"]
            else:
                print("Please only insert a level between 1 and 20")
                sys.exit(1)
        else:
            print(
                "Invalid level type\nPlease only insert an integer or a range with the syntax X-Y"
            )
            sys.exit(1)  # Probably unreachable, but type safety y'know

    money["currency"] += Money(gp=currency, origin="currency")

    # Convert coins in gp where possible, if requested
    if not noconversion:
        for origin in money.keys():
            money[origin].gp += money[origin].cp // 100
            money[origin].gp += money[origin].sp // 10
            money[origin].cp %= 100
            money[origin].sp %= 10

    def get_total(money_list):
        res = Money(origin="Total", check_origin=False)
        for item in money_list:
            res += item
        return res

    money["total"] = get_total(money.values())

    print("Total value", end="")
    if not noconversion:
        print(" (converted in gp)", end="")
    print(":")
    print(
        textwrap.dedent(
            f"""{money["total"].cp} cp
            {money["total"].sp} sp
            {money["total"].gp} gp

        Of which:
            Items: {money["item"].gp} gp
            Currency: {money["currency"].gp} gp
        """
        )
    )

    if level:
        print("Difference:")
        if total_value - money["total"].gp < 0:
            print(
                f"    {abs(total_value - money['total'].gp)} gp too much (Expected {total_value} gp)\n"
            )
        elif total_value - money["total"].gp > 0:
            print(
                f"    {abs(total_value - money['total'].gp)} gp too little (Expected {total_value} gp)\n"
            )
        else:
            print(f"    None (Expected {total_value} gp)\n")

    print("Levels:")
    for lvl, amount in levels.items():
        print(f"    Level {lvl}: {amount}")

    print("\nCategories:")
    for cat, amount in categories.items():
        if cat:
            print(f"    {cat.capitalize()}: {amount}")
        else:
            print(f"    None: {amount}")

    print("\nRarities:")
    for rar, amount in rarities.items():
        print(f"    {rar.capitalize()}: {amount}")

    sys.exit(0)


def entry_point():
    parser = argparse.ArgumentParser(
        description="A simple tool for Pathfinder 2e that calculates how much your loot is worth."
    )
    parser.add_argument(
        "input",
        type=str,
        nargs="?",
        default="",
        help="the name of the text file containing the loot",
    )
    parser.add_argument(
        "-l",
        "--level",
        type=str,
        help="the level of the party; can be an integer or of the form X-Y (eg. 5-8)",
    )
    parser.add_argument(
        "-c",
        "--currency",
        type=int,
        default=0,
        help="a flat amount of gp to add to the total",
    )
    parser.add_argument(
        "-f",
        "--format",
        action="store_true",
        help="show formatting instructions and exit",
    )
    parser.add_argument(
        "-n",
        "--no-conversion",
        action="store_true",
        help="prevent conversion of coins into gp",
    )
    args = parser.parse_args()

    if args.format:
        # Add more info in the formatting instructions
        print(
            textwrap.dedent(
                """\
            [TEXT FILE FORMAT]
            The text file must contain two comma-separated columns:
            The first is the item name, which is case insensitive but requires correct spelling
            The second is the amount of items you want to add and must be a positive integer
            This means that each row is an item name and how many there are
            The amount can be omitted, in which case it'll default to 1

            [VALID ITEM NAMES]
            The item name must use the spelling used on the Archives of Nethys
            If the item has a grade, it must added in brackets after the name
            For instance, "smokestick (lesser)" is correct, "lesser smokestick" is not

            The item name can also be an item with runes etched into it and the price will be calculated automatically
            "+1 striking longsword" is a valid name, as is "+3 major striking greater shock ancestral echoing vorpal glaive"
            For runes specifically, the grade must be placed before the rune itself, as you would write normally
            It should be "+2 greater striking longbow" and not "+2 striking (greater) longbow"

            The item can also include a precious material, though you must specify the grade
            The grade must be after the item name and simply needs to include "low", "standard" or "high"
            "silver dagger (low-grade)" is correct, as is "silver dagger low"
            Make sure that it's only one word: "high-grade" is ok, "high grade" is not
            Remember that not every material supports every grade; invalid grades currently crash the program

            Runes and precious materials can be combined in one single name
            "+1 striking mithral warhammer (standard)" is valid

            The item can also be plain currency, though you still need to specify the amount
            "32gp" is a valid item name
            Accepted currencies are "cp", "sp" and "gp"; "pp" in not supported

            [SAMPLE FILE]
            longsword,1
            oil of potency,2
            smokestick (lesser),5
            32sp,1
            +1 striking shock rapier,1
            storm flash,1
            cold iron warhammer (standard),1

            [LEVEL RANGES]
            Levels can be input both as a single value (like "1") and as a range (like "1-6")
            A single value represents the amount of treasure that the players should find over the course of that level
            A range instead represents the amount of treasure expected for that range of levels
            For example, "1" is how much treasure should be given to the PCs progressing through level 1
            while "1-3" refers to how much treasures should be given throughout levels 1, 2 and 3
            The values are taken from the Treasure by Level table on page 508 of the Core Rulebook
            On Archives of Nethys: https://2e.aonprd.com/Rules.aspx?ID=581\
            """
            )
        )
        sys.exit(0)

    if os.path.isfile(args.input) and args.input.endswith(".txt"):
        console_entry_point(args.input, args.level, args.currency, args.no_conversion)
    else:
        print("Please input a valid text file")
        sys.exit(1)


if __name__ == "__main__":
    entry_point()
