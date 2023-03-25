from pf2e_wealth_calculator.pf2ewc import (
    find_single_item,
    console_entry_point,
    generate_random_items,
)
from pf2e_wealth_calculator.dataframes import tbl

from tabulate import tabulate

import argparse
import textwrap
import sys
import os


def entry_point():
    parser = argparse.ArgumentParser(
        description="A simple tool for Pathfinder 2e that calculates how much your loot is worth."
    )
    parser.add_argument(
        "input",
        type=str,
        nargs="*",
        default="",
        help="the name of the text file containing the loot",
    )
    parser.add_argument(
        "-i",
        "--item",
        type=str,
        help="run the script with only the specified item and exit",
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
        "-d",
        "--detailed",
        action="store_true",
        help="show more information about the items than usual",
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
    parser.add_argument(
        "-r",
        "--random",
        type=int,
        help="randomly pick items within a range of levels"
    )
    parser.add_argument(
        "--tbl",
        action="store_true",
        help="print the Treasure by Level table and exit"
    )
    args = parser.parse_args()

    if args.format:
        # TODO: Add more info in the formatting instructions
        print(
            textwrap.dedent(
                """\
            [TEXT FILE FORMAT]
            The text file must contain two comma-separated columns:
            The first is the item name, which is case insensitive
            The second is the amount of items you want to add and must be a positive integer
            The amount can be omitted, in which case it'll default to 1
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
            "32gp" is a valid item name
            Accepted currencies are "cp", "sp" and "gp"; "pp" in not supported
            You can add an asterisk before the currency to have it be considered as an art object

            [COMMENTS]
            You can comment lines by adding a # at the start of the line

            [SAMPLE FILE]
            longsword
            oil of potency, 2
            smokestick (lesser), 5
            32sp
            +1 striking shock rapier
            storm flash
            cold iron warhammer (standard)

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

    if args.tbl:
        print(
            tabulate(
                tbl, # type: ignore
                headers=tbl.columns, # type: ignore
                showindex=False,
                tablefmt="rounded_outline",
            )
        )
        sys.exit(0)

    if args.item:
        find_single_item(args.item)
        sys.exit(0)

    if args.random:
        if args.level:
            generate_random_items(args.random, args.level)
        else:
            generate_random_items(args.random)

        sys.exit(0)

    if all(os.path.isfile(file) for file in args.input) and all(
        file.endswith(".txt") for file in args.input
    ):
        console_entry_point(
            args.input, args.level, args.currency, args.detailed, args.no_conversion
        )
        sys.exit(0)
    else:
        print("Please input a valid text file or use the -i or -r options")
        sys.exit(1)


if __name__ == "__main__":
    entry_point()
