# PF2e Wealth Calculator
![tests-badge](https://github.com/D4wnstar/pf2e-wealth-calculator/actions/workflows/tests.yml/badge.svg)

A simple tool to quickly get information on large batches of items for Pathfinder Second Edition.

## Prerequisites

- Python 3.10 or above

## Usage

Write a text file with two comma-separated columns.\
In the first one, write the names of the items.\
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

It should produce the following output:

```
Total value (converted in gp):
0 cp
4 sp
29 gp

Of which:
Items: 17 gp
Currency: 12 gp

Levels:
Level 0: 4
Level 1: 5

Categories:
Weapons: 1
Alchemical items: 5
Adventuring gear: 2
Currency: 1

Rarities:
Common: 9
```

You can use the `-l` or `--level` option followed by the party's level or two levels in the format X-Y to compare the items' total value to the one PCs are supposed to come across throughout the level or range of levels you input. These expected values come from the Treasure by Level table on Page 508 of the Core Rulebook (which you can find [here](https://2e.aonprd.com/Rules.aspx?ID=581)).

For instance, running

```
pf2ewc your_text_file.txt -l 1
```

would add the following lines to the previous output:

```
Difference:
146 gp too little (Expected 175 gp)
```

### Other options

`-c` or `--currency` followed by a number adds an arbitrary amount of gp to the calculation

`-f` or `--format` prints helpful information on how correctly format the text file

`-n` or `--no-conversion` prevents coins from being converted to gp automatically (some calculations use gp only, so expect values to be slightly different from what you'd expect)

## License

This project is released under the [GNU GPLv3 License](https://github.com/D4wnstar/pf2e-wealth-calculator/blob/develop/LICENSE).