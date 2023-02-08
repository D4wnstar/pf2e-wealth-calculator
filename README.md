# PF2e Wealth Calculator
![tests-badge](https://github.com/D4wnstar/pf2e-wealth-calculator/actions/workflows/tests.yml/badge.svg)

A simple tool to quickly get information on large batches of items, runes and precious materials for Pathfinder Second Edition.

## Prerequisites

- Python 3.9 or above

## Installation

- Python (Recommended method)
    - If you already have Python installed, simply run `pip install pf2e-wealth-calculator`
    - > If you encounter an error, try changing `pip` to `pip3`.
    - If you don't already have Python installed, you can get it from the [official website](https://www.python.org/downloads/), your operating system's package manager or the Microsoft Store.

- Prebuilt Windows Executable
    - If you are on Windows and don't want to install Python, you can download the executable file directly from the [Releases Tab](https://github.com/D4wnstar/pf2e-wealth-calculator/releases).
    - If you choose this method, don't double click on the executable file to use it! It won't work. Instead, place it in a folder of your preference, then open a terminal in that folder (in Windows 11 you can just right click on the folder and press "Open in Terminal"). Follow the same instructions under Usage, except you change every `pf2ewc` to the name of the executable prefixed by `.\`. For example, if you downloaded `pf2ewc-0.1.0.exe`, you can use `.\pf2ewc-0.1.0.exe`

## Usage

There's two ways to use this script: either pass in an item name directly or make a text file containing a list of items and how many of each you want.

To pass a single item, simply run

```
pf2ewc -i "your item here"
```

Alternatively, create and write a text file with two comma-separated columns.

In the first column, write the names of the items.

In the second, write how many of each item you want. This can be omitted, in which case the default is 1.

For example:

```
Longsword, 1
Sunrod, 5
Lantern (Hooded), 2
12gp
```

Then open a terminal in the same folder as the text file and run

```
pf2ewc your_text_file.txt
```

If you used the previous items, it should produce the following output:

```
Total value (converted in gp):
  - 0 cp
  - 4 sp
  - 29 gp

Of which:
  - Items: 17 gp
  - Currency: 12 gp
```

You can use the `-l` or `--level` option followed by the party's level or two levels in the format X-Y (e.g. 2-5) to compare the items' total value to the one PCs are supposed to come across throughout the level or range of levels you input. These expected values come from the Treasure by Level table on Page 508 of the Core Rulebook (which you can find [here](https://2e.aonprd.com/Rules.aspx?ID=581)).

For instance, running

```
pf2ewc your_text_file.txt -l 1
```

would add the following lines to the previous output:

```
Difference:
  - 146 gp too little (Expected 175 gp)
```

If you want a detailed breakdown of what you're giving to your players, then you can use the `-d` or `--detailed` option, which counts the levels, categories, subcategories and rarities of all of the items you input.

Using the same items as before with the `-d` option would add these line to the output:

```
Levels:
  - Level 0: 4
  - Level 1: 5

Categories:
  - Weapons: 1
  - Alchemical items: 5
  - Adventuring gear: 2
  - Currency: 1

Subcategories:
  - Base weapons: 1
  - Alchemical tools: 5
  - None: 3

Rarities:
  - Common: 9
```

## Formatting guidelines

> You can also print these rules in the terminal by using `pf2ewc -f`.

- PF2e Wealth Calculator is entirely case-insensitive, meaning it doesn't matter if the names of the items are uppercase or lowercase.
- In the majority of cases, the spelling must be exactly the same as the one used by the Archives of Nethys (this is because this calculator uses data from the AoN). A spelling mistake will cause the script to skip the item and suggest a possible correction. Other items in the file will still be processed.
- You can input a weapon or armor with runes etched into it and the script will automatically calculate the price, level and rarity of the item. The calculator is built with standard notation in mind, meaning it should start with the potency rune (i.e. the +1/+2/+3), followed by the striking and potency runes (if any), followed by the item itself. For instance, `+1 striking warhammer` is fine, as is `+2 greater striking frost extending halberd`. Runes ordered in a different manner usually work so long they all precede the base item, but such syntax is not officially supported.
- You can also input weapons, armor and items made of a precious material. As with runes, the price, level and rarity will be calculated automatically. Write the item name as you would usually: this means the material goes first, then the base item and finally the grade of the material. For example, `silver dagger (low-grade)` is correct. To cut down on typing, the grade really just needs to include "low", "standard" or "high" and it'll be treated the same way; `silver dagger low` will work just fine. One thing to note is that most materials can only be found at higher grades. This script _does not_ check if the material/grade pair is valid and _will_ crash if it's not.
- You can combine runes and materials too! Just make sure that _all_ of the runes are placed before the material and the item, otherwise it won't work. Otherwise, follow the syntax from the previous two points. For example, `+1 striking ghost touch mithral flail (standard-grade)` is correct.
- Currency is a valid item to input, which is useful in case you want to make your players find a bunch of plain old coins in a dungeon, for instance. The syntax is just what you'd expect: the number of coins followed by the coin type. `12 gp` and `520cp` are both accepted examples. Note that platinum pieces ("pp") are not supported.

## Options

`-l` or `--level` followed by a number or two numbers in the X-Y format makes the calculator compare the total value of the input items to the expected total value that a party of four is supposed to find throughout the specified level(s).

`-c` or `--currency` followed by a number adds an arbitrary amount of gp to the calculation.

`-f` or `--format` prints helpful information on how to correctly format the text file.

`-n` or `--no-conversion` prevents coins from being converted to gp automatically (some calculations use gp only, so expect values to be slightly different from what you'd expect).

`-i` or `--item` followed by the name of an item allows you to run the script without creating a file. If the item name is composed of multiple words, you must put it in quotation marks, like `-i "tengu gale blade"`.

## Known issues

- Custom scrolls and wands are not supported. However, since their price only varies with spell level, you can use their general item names instead. For scrolls it's `nth-Level Scroll` and for wands it's `Magic Wand (nth-Level Spell)`, where "nth" is the spell's level (e.g. 1st, 2nd, etc.). For example, instead of `scroll of lightning bolt`, use `3rd-level scroll` and instead of `wand of see invisibility`, use `magic wand (2nd-level spell)`.
- Precious material price calculation does not currently take item Bulk into account. This means that the actual cost of the item is often underestimated by 10% or 20%.
- There is currently no way to apply runes to anything that doesn't use potency runes. This means accessories and shields with runes are currently not supported. To get around this, you can add the runes as separate items, which would give the same total value at the cost of not getting the correct item level and rarity.

## License

This project is released under the [GNU GPLv3 License](https://github.com/D4wnstar/pf2e-wealth-calculator/blob/master/LICENSE). The data this program parses through is taken from the [Archives of Nethys](https://2e.aonprd.com/) and is available for use under the [Open Game License v1.0a](https://github.com/D4wnstar/pf2e-wealth-calculator/blob/master/OGL).