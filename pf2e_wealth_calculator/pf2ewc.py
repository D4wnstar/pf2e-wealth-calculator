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
    """
    Simple data structure for cp/sp/gp amounts.
    """
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
                self.check_origin)

        if type(val) == Money:
            if self.check_origin and val.check_origin and self.origin != val.origin:
                raise ValueError("Origins don't match")
            return Money(
                self.cp + val.cp,
                self.sp + val.sp,
                self.gp + val.gp,
                self.origin,
                self.check_origin)

        raise TypeError(
            f"Unsupported sum operation for type {type(val)} on class Money")

    def __radd__(self, val):
        return self.__add__(val)


@dataclass(frozen=True)
class ItemInfo:
    """
    Data structure that contains information on a given item.
    """
    name: str = "item"
    price: Money = Money()
    category: str | None = None
    level: int = 0
    rarity: str = "common"


def get_higher_rarity(rar1: str, rar2: str) -> str:
    ordering = {
        "common": 1,
        "uncommon": 2,
        "rare": 3
    }

    rarnum1 = ordering[rar1]
    rarnum2 = ordering[rar2]

    return rar1 if rarnum1 > rarnum2 else rar2


def parse_database(
        item_name: str,
        amount: int,
        *,
        restrict_cat: str | None = None,
        df: pd.DataFrame = itemlist,
        materials: list[str] = materials,
        quiet: bool = False) -> ItemInfo:
    """Parses the Archives of Nethys item list and returns information about the item."""

    is_currency = get_price(item_name, amount)
    item_name = item_name.strip()

    # Check if it's plain currency, in which case short-circuit
    if is_currency != Money():
        is_currency.origin = "currency"
        return ItemInfo(item_name, is_currency, "currency")

    material: str | None = None
    grade: str | None = None

    # Check if the first one or two words denote a precious material
    name_list = item_name.split(" ")
    if name_list[0] in materials:
        material = name_list.pop(0)
        grade = name_list.pop(-1)

        if "low" in grade:
            grade = "(low-grade)"
        elif "standard" in grade:
            grade = "(standard-grade)"
        elif "high" in grade:
            grade = "(high-grade)"

        item_name = " ".join(name_list)
    elif " ".join(name_list[0:2]):
        try:
            if name_list[0] + " " + name_list[1] in materials:
                material = name_list[0] + " " + name_list[1]
                del name_list[0:2] # TODO: Change to pop
                grade = name_list.pop(-1)

                if "low" in grade:
                    grade = "(low-grade)"
                elif "standard" in grade:
                    grade = "(standard-grade)"
                elif "high" in grade:
                    grade = "(high-grade)"

                item_name = " ".join(name_list)
        except IndexError:
            pass

    if restrict_cat:
        filtered_list = itemlist.set_index('category')
        filtered_list = filtered_list.filter(like=restrict_cat, axis=0)
        item_row = filtered_list[filtered_list["name"] == item_name]
    else:
        item_row = df[df["name"] == item_name]

    # If there is no item with the given name, find closest item to suggest
    # and print a warning
    if item_row.empty:
        if not quiet:
            suggestion = "".join(get_close_matches(
                item_name.strip(), df["name"].tolist(), 1, 0))
            print(
                f'WARNING: Ignoring item "{item_name}". Did you mean "{suggestion}"?')

        return ItemInfo(item_name, category="error")

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
        }
        material_name = f"{material} {categories[item_category]} {grade}"

        # Add the price of the precious material
        item_price = get_price(
            df[df["name"] == material_name]["price"].item(), amount)

        # Materials have their own level and rarity, pick the highest ones
        material_level = df[df["name"] == material_name]["level"].item()
        item_level = material_level if material_level > item_level else item_level

        material_rarity = df[df["name"] == material_name]["rarity"].item()
        item_rarity = get_higher_rarity(material_rarity, item_rarity)

    return ItemInfo(
        item_name,
        item_price,
        item_category,
        item_level,
        item_rarity)


def get_potency_rune_stats(cached_rune: str, category: str | None, level: int) -> tuple[Money, int]:
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
            case _: raise ValueError("Invalid potency rune.")

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
            case _: raise ValueError("Invalid potency rune.")

    else:
        return Money(), level


def rune_calculator(
        item_name,
        amount,
        df: pd.DataFrame = itemlist,
        rune_names: pd.DataFrame = rune_replacer,
        materials: list[str] = materials) -> ItemInfo:
    """Automatically breaks down the item's name into singular runes and returns the total price as a Money object."""

    def check_multiword_item(item, amount, item_runes, cur_index):
        # increment = 1

        # while True:
        #     try:
        #         # Iteratively append the following runes in the item name until
        #         # it finds something
        #         item += " " + item_runes[cur_index + increment]
        #         item_info = parse_database(item, amount, quiet=True)
        #         if item_info.category != "error":  # If it finds something, continue with price calculation and finish loop
        #             # Non-rune items must always be at the end of the name,
        #             # thus it's guaranteed there's nothing left
        #             return item_info
        #         increment += 1

        #     except IndexError:
        #         return ItemInfo(item_name, category="error")

        item += " " + " ".join(item_runes[cur_index+1:])
        item_info = parse_database(item, amount, quiet=True)
        if item_info.category != "error":
            return item_info
        else:
            return ItemInfo(item, category="error")

    running_sum = Money()
    highest_level = 0
    highest_rarity = "common"
    item_runes = item_name.split()  # Break up the name into single runes
    potency_rune = "0"
    skip_cycle = False

    rune_info = ItemInfo()  # Define early for type safety

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
            highest_level = rune_info.level if rune_info.level > highest_level else highest_level
            highest_rarity = get_higher_rarity(
                highest_rarity, rune_info.rarity)
            skip_cycle = True
            continue

        # Replace the name if necessary. If it is replaced, replace and short-circuit cycle
        rune_row = rune_names[rune_names["name"] == rune]
        if not rune_row.empty and len(rune_row["replacer"].item()) > 0:
            rune_info = parse_database(
                rune_row["replacer"].item(), amount, quiet=True)
            running_sum += rune_info.price
            highest_level = rune_info.level if rune_info.level > highest_level else highest_level
            highest_rarity = get_higher_rarity(
                highest_rarity, rune_info.rarity)
            skip_cycle = True
            continue
        elif not rune_row.empty and len(rune_row["replacer"].item()) == 0:
            continue

        # Find the rune in the list of runes (if present)
        if rune not in materials:
            rune_info = parse_database(
                rune, amount, df=df, materials=materials, restrict_cat='runes', quiet=True)
        else:
            rune_info = ItemInfo(rune, category="error")

        # If it's not in the list, or it's a material, it might be a multi-word item name or a precious material
        # It's guaranteed to not be a rune because of the rune name replacer
        if rune_info.category == "error":
            rune_info = check_multiword_item(
                rune, amount, item_runes, cur_index)
            if rune_info.category != "error":
                highest_level = rune_info.level if rune_info.level > highest_level else highest_level
                highest_rarity = get_higher_rarity(
                    highest_rarity, rune_info.rarity)
                running_sum += rune_info.price
                break
            else:
                print(
                    f"WARNING: No results for {item_name}. Skipping price calculation.")
                return ItemInfo(item_name, category="error")
        else:
            highest_level = rune_info.level if rune_info.level > highest_level else highest_level
            highest_rarity = get_higher_rarity(
                highest_rarity, rune_info.rarity)

        # Add rune/base item price to the total
        running_sum += rune_info.price

    # Manually change the grade tag into the standardized form
    for grade in ["low", "standard", "high"]:
        if grade in item_runes[-1]:
            item_runes[-1] = f"({grade}-grade)"
            item_name = " ".join(item_runes)

    # Add potency rune price
    add_to_sum, highest_level = get_potency_rune_stats(
        potency_rune, rune_info.category, highest_level)
    running_sum += add_to_sum
    return ItemInfo(item_name, running_sum, rune_info.category, highest_level, highest_rarity)


def get_price(price_str: str, amount: int) -> Money:
    """
    Get the price of the given item.

    price_str is a string that includes the price and coin type (i.e. "12 gp").

    amount is an integer that multiplies the price of the given item before adding it.
    """

    # Fetch price and coin type through regex
    item_match = (re.search(r"\d*(,\d*)?", price_str))
    coin_match = re.search(r"cp|sp|gp", price_str)

    # Check which kind of coin it is (if any)
    if coin_match is not None and item_match is not None:
        # Add to total while multiplying by quantity
        item_price = item_match.group()
        coin_type = coin_match.group()

        match coin_type:
            # Regex is totally unnecessary but whatever lmao
            case "cp": return Money(int(re.sub(",", "", item_price)) * amount, 0, 0)
            case "sp": return Money(0, int(re.sub(",", "", item_price)) * amount, 0)
            case "gp": return Money(0, 0, int(re.sub(",", "", item_price)) * amount)
            # This shouldn't even be reachable
            case _: raise ValueError("Invalid currency type")
    else:
        return Money()


def console_entry_point(input_file, level, currency):
    # User-defined loot
    loot = pd.read_csv(input_file, names=["name", "amount"])
    loot["name"] = loot["name"].apply(lambda name: name.lower())
    # Assume no amount means 1
    loot["amount"].fillna(1, inplace=True)
    # Uses regex to replace non-numeric values in the "Amount" column
    loot["amount"].replace(r"\D", 0, regex=True, inplace=True)
    loot["amount"] = loot["amount"].astype(int)

    money = {
        "item": Money(origin="item"),
        "currency": Money(origin="currency")
    }

    # Get the price for each item
    for _, row in loot.iterrows():
        # Check if there is a fundamental rune in the item
        if "+1" in row["name"] or "+2" in row["name"] or "+3" in row["name"]:
            curr_item = rune_calculator(row.tolist()[0], row.tolist()[1])
            money[curr_item.price.origin] += curr_item.price
        else:
            curr_item = parse_database(row.tolist()[0], row.tolist()[1])
            money[curr_item.price.origin] += curr_item.price

    if level is None:
        # If no level is passed, ask for it interactively
        while True:
            try:
                level = input(
                    "Enter the party's level or a range of levels (e.g. 5-8): ")
                split = level.split("-")
                if [level] == split:
                    level = int(level)
                else:
                    level = [int(x) for x in split]

            except ValueError:
                print("Please only insert an integer or a range with the syntax X-Y.")

            else:
                if type(level) is list:
                    if 0 < level[0] <= 20 and 0 < level[1] <= 20:
                        # Get total value from the TBL table
                        total_value = tbl["Total Value"][min(
                            level) - 1:max(level) - 1].sum()
                        break
                    else:
                        print("Please only insert levels between 1 and 20")
                elif type(level) is int:
                    if 0 < level <= 20:
                        # Get total value from the TBL table
                        total_value = tbl.at[level - 1, "Total Value"]
                        break
                    else:
                        print("Please only insert a level between 1 and 20")
    else:
        # Check if the input is a positive scalar integer
        try:
            if int(level) < 0:
                print("Please only insert levels between 1 and 20")
                sys.exit(1)
        except ValueError:
            pass

        # Check if every input value is a valid scalar integer
        split = level.split("-")
        try:
            map(int, split)
        except ValueError:
            print(
                "Invalid level type.\nPlease only insert an integer or a range with the syntax X-Y.")
            sys.exit(1)

        if [level] == split:
            level = int(level)
        else:
            level = [int(x) for x in split]

        if type(level) is list:
            if 0 < level[0] <= 20 and 0 < level[1] <= 20:
                # Get total value from the TBL table
                total_value = tbl["Total Value"][min(
                    level) - 1:max(level) - 1].sum()
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
                "Invalid level type.\nPlease only insert an integer or a range with the syntax X-Y.")
            sys.exit(1)  # Probably unreachable, but type safety y'know

    money["currency"] += Money(gp=currency, origin="currency")

    # Convert coins in gp where possible
    for origin in money.keys():
        money[origin].gp += int(money[origin].cp / 100)
        money[origin].gp += int(money[origin].sp / 10)
        money[origin].cp %= 100
        money[origin].sp %= 10

    def get_total(money_list):
        res = Money(origin="Total", check_origin=False)
        for item in money_list:
            res += item
        return res

    money["total"] = get_total(money.values())

    print(textwrap.dedent(f"""
            Total value (converted in gp):
                {str(money["total"].cp)} cp
                {str(money["total"].sp)} sp
                {str(money["total"].gp)} gp

            Of which:
                Items: {money["item"].gp} gp
                Currency: {money["currency"].gp} gp
            """))

    print("Difference:")
    if total_value - money["total"].gp < 0:
        print(
            f"{abs(total_value - money['total'].gp)} gp too much (Expected: {total_value} gp)")
    elif total_value - money["total"].gp > 0:
        print(
            f"{abs(total_value - money['total'].gp)} gp too little (Expected: {total_value} gp)")
    else:
        print(f"None (Expected: {total_value} gp)")

    sys.exit(0)


def entry_point():
    parser = argparse.ArgumentParser(
        description="A simple tool for Pathfinder 2e to calculate how much your loot is worth.")
    parser.add_argument("input", type=str, nargs='?', default='',
                        help="the name of the text file containing the loot")
    parser.add_argument(
        "-l",
        "--level",
        type=str,
        help="the level of the party; can be an integer or of the form X-Y (eg. 5-8)")
    parser.add_argument("-c", "--currency", type=int, default=0,
                        help="a flat amount of gp to add to the total")
    parser.add_argument(
        "-f",
        "--format",
        action="store_true",
        help="show formatting instructions for the text file and exit")
    args = parser.parse_args()

    if args.format:
        # Add more info in the formatting instructions
        print(textwrap.dedent("""
            [TEXT FILE FORMAT]
            The text file must contain two comma-separated columns:
            The first is the item name, which is case insensitive but requires correct spelling
            The second is the amount of items you want to add and must be a positive integer
            This means that each row is an item name and how many there are

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
            "32gp" is a valid item name, but the second column must still be filled with a number
            Accepted currencies are "cp", "sp" and "gp". "pp" in not supported

            [EXAMPLE]
            longsword,1
            oil of potency,2
            smokestick (lesser),5
            32sp,1
            +1 striking shock rapier,1
            storm flash,1
            cold iron warhammer (standard),1
            """))
        sys.exit(0)
    elif os.path.isfile(args.input) and args.input.endswith(".txt"):
        console_entry_point(args.input, args.level, args.currency)
    else:
        print("Please input a valid text file.")
        sys.exit(1)


if __name__ == "__main__":
    entry_point()


# -----------------#
#   NEEDS FIXING   #
# -----------------#
# Nothing urgent :)


# TODO
# [DONE] Allow adding an arbitrary amount of gold for plain wealth
# [DONE] Check what happens if you add a comma but no quantity (i.e. tindertwig, )
# [DONE] Add support for dynamic rune price calculation (i.e. auto-calculate price of +1 striking keen warhammer). Maybe use that all items with runes must start with a +
# [DONE] Add support for calculating wealth only for a specific (range of) level(s), instead of all of them up to the user input
# [DONE] Maybe change item_info type to dict or custom data structure
# Print how many items of a given level, category and rarity there are
# Add different verbosity levels
# Add support for multiple file input, which calculates the value of all of the items in every file. Useful, for instance, to keep loot for each level or area separate
# Add description of how levels/level ranges work in the help description
# Add switch to autocorrect spelling mistakes instead of just suggest corrections
# Make amount column optional (default is 1)

# KNOWN ISSUES:
# Handwraps of mighty blows don't have a listing in the item list without runes: add special warning about that
# Wands and scrolls don't have a listing, however their naming scheme is standardized so they can be automated
# Add dragon's breath rune and called rune handling
# Precious item cost is wrong as it doesn't take Bulk into account. Currently unfixable because I can't get new CSV tables from the AoN
