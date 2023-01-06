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
			return Money(self.cp + val, self.sp + val, self.gp + val, self.origin, self.check_origin)
		elif type(val) == Money:
			if self.check_origin and self.origin != val.origin:
				raise ValueError("Origins don't match")
			return Money(self.cp + val.cp, self.sp + val.sp, self.gp + val.gp, self.origin, self.check_origin)
		else:
			raise TypeError(f"Unsupported sum operation for type {type(val)} on class Money")
	
	def __radd__(self, val):
		return self.__add__(val)


# Helper function to allow a variable amount of return values
def mask_list(list, mask):
	res = []
	for item, flag in zip(list, mask):
		if flag:
			res.append(item)
	
	if len(res) == 1:
		return res[0]
	else:
		return res

def parse_database(item_name: str, amount: int, df: pd.DataFrame, materials: list, *,
				   price: bool=True, category: bool=False, level: bool=False, rarity: bool=False,
				   quiet: bool=False) -> Money | str | int | list:
	"""Parses the Archives of Nethys item list and returns information about the item."""

	# Check if there is at least something to return
	flags = [price, category, level, rarity]
	if not any(flags):
		raise ValueError("At least one flag argument must be True")

	is_currency = get_price(item_name, amount)

	# Check if it's plain currency, in which case short-circuit
	if is_currency:
		is_currency.origin = "currency"
		return mask_list([is_currency, "Currency", -1, "None"], flags)

	material = False

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
	else:
		try:
			if name_list[0] + " " + name_list[1] in materials:
				material = name_list[0] + " " + name_list[1]
				del name_list[0:2]
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

	item_row = df[df["Name"] == item_name.strip()]

	# If there is no item with the given name, find closest item to suggest and print a warning
	if item_row.empty:
		if not quiet:
			suggestion = "".join(get_close_matches(item_name.strip(), df["Name"].tolist(), 1, 0))
			print(f'WARNING: Ignoring item "{item_name}". Did you mean "{suggestion}"?')
		return mask_list([Money(), "Error", -1, "None"], flags)

	item_category = item_row["Category"].item()
	item_level = item_row["Level"].item()
	item_rarity = item_row["Rarity"].item()

	# Get item price
	if not material:
		item_price = get_price(item_row["Price"].item(), amount)
	else:
		# Convert category to a code-legible string
		categories = {
			"Weapons": "weapon",
			"Armor": "armor",
			"Shields": "shield",
			"Materials": "object",
			"Adventuring Gear": "object"
		}

		# Add the price of the precious material
		item_price = get_price(df[df["Name"] == f"{material} {categories[item_category]} {grade}"]["Price"].item(), amount)

		# Add the price of the base item
		item_price += get_price(item_row["Price"].item(), amount)


	return mask_list([item_price, item_category, item_level, item_rarity], flags)
		

def rune_calculator(item_name, amount, df: pd.DataFrame, runelist: pd.DataFrame, rune_names: pd.DataFrame,
					materials: pd.DataFrame, *, price: bool=True, category: bool=False, level: bool=False,
					rarity: bool=False) -> Money | str | int | list:
	"""Automatically breaks down the item's name into singular runes and returns the total price as a Money object."""

	# Helper function to make potency rune handling easier
	def get_cached_rune_price(cached_rune: str, category: str) -> Money:
		"Use the cached potency rune to add the appropriate price, depending on category"

		if category == "Weapons":
			match cached_rune:
				case "+1": return Money(0, 0, 35)
				case "+2": return Money(0, 0, 935)
				case "+3": return Money(0, 0, 8935)

		elif category == "Armor":
			match cached_rune:
				case "+1": return Money(0, 0, 160)
				case "+2": return Money(0, 0, 1060)
				case "+3": return Money(0, 0, 20560)

		else:
			return Money()

	running_sum = Money()
	item_runes = item_name.split() # Break up the name into single runes
	potency_rune = "0"
	cur_index = 0
	breaker = False
	flags = [price, category, level, rarity]

	# Cycle through runes found in the item name
	for cur_index, rune in enumerate(item_runes):
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

		# Handle rune prefixes manually
		if rune in ("lesser", "moderate", "greater", "major", "true"):
			rune = f"{item_runes[cur_index + 1]} ({rune})"
			del item_runes[cur_index + 1]

		# Check if the name needs to be replaced
		rune_row = rune_names[rune_names["Name"] == rune]
		if not rune_row.empty:
			rune = rune_row["Replacer"].item()
			if rune == "":
				continue

		if rune not in materials:
			# Find the rune in the list of runes (if present)
			# item_row = runelist[runelist["Name"] == rune]
			item_info = parse_database(rune, amount, runelist, materials, price=True, category=True, level=True, rarity=True, quiet=True)

			# If it's not in the list of runes, check if it's another item
			# if item_row.empty:
				# item_row = df[df["Name"] == rune]
			if item_info[1] == "Error":
				item_info = parse_database(rune, amount, df, materials, price=True, category=True, level=True, rarity=True, quiet=True)
		else:
			item_info = [0, "Error"]

		# If it's again not in the list, it might just be a multi-word item name or a precious material
		# It's guaranteed to not be a rune as it already checked in the rune list
		if item_info[1] == "Error":
			new_rune = rune # Preserves original rune name to allow for proper error messages
			increment = 1

			while True:
				try:
					new_rune += " " + item_runes[cur_index + increment] # Iteratively append the following runes in the item name until it finds something
					# item_row = df[df["Name"] == new_rune]
					item_info = parse_database(new_rune, amount, df, materials, price=True, category=True, level=True, rarity=True, quiet=True)
					if item_info[1] != "Error": # If it finds something, continue with price calculation and finish loop
						breaker = True # Non-rune items must always be at the end of the name, thus it's guaranteed there's nothing left
						break
					increment += 1

				# Once nothing is left, check database if it can find the item
				# This is necessary to handle precious materials
				except IndexError:
					if item_info[0] == Money():
						print(f"WARNING: No results for {item_name}. Skipping price calculation.")
						return mask_list([Money(), "Error", -1, "None"], flags)
					else:
						running_sum += item_info[0]
						running_sum += get_cached_rune_price(potency_rune, item_info[1])
						item_info[0] = running_sum
						return mask_list(item_info, flags)

		# Add rune/base item price to the total
		running_sum += item_info[0]

		if breaker:
			break

	# Add potency rune price
	running_sum += get_cached_rune_price(potency_rune, item_info[1])
	return running_sum


def get_price(price_str: str, amount: int, *, money: Money=None) -> Money | bool:
	"""
	Gets the price of the given item and optionally adds it to the given Money object.

	item_row is a string that includes the price and coin type (i.e. 12 gp).

	amount is an integer that multiplies the price of the given item before adding it.

	money is a Money object.
	"""

	# Fetch price and coin type through regex
	item_price = (re.search("\d*(,\d*)?", price_str)).group()
	coin_type = re.search("cp|sp|gp", price_str)

	# Check which kind of coin it is (if any)
	if coin_type is not None:
		# Add to total while multiplying by quantity
		if money is None:
			match coin_type.group():
				case "cp": return Money(int(re.sub(",", "", item_price)) * amount, 0, 0)
				case "sp": return Money(0, int(re.sub(",", "", item_price)) * amount, 0)
				case "gp": return Money(0, 0, int(re.sub(",", "", item_price)) * amount)
		else:
			match coin_type.group():
				case "cp": money.cp += int(re.sub(",", "", item_price)) * amount # Regex is totally unnecessary but whatever lmao
				case "sp": money.sp += int(re.sub(",", "", item_price)) * amount
				case "gp": money.gp += int(re.sub(",", "", item_price)) * amount
	else:
		return False

def console_entry_point(input_file, level, currency):
	# Read the necessary files
	pathfinder = lambda path : os.path.join(os.path.dirname(os.path.realpath(__file__)), path)
	table = pd.read_csv(pathfinder("tables/PF2eItemList.csv"), dtype={'Level': int}) # List of all items
	runes = pd.read_csv(pathfinder('tables/runes.csv')) # List of just runes
	rune_names = pd.read_csv(pathfinder('tables/rune_names.csv')) # Rune name translation table
	tbl = pd.read_csv(pathfinder('tables/treasurebylevel.csv')) # Treasure by level table
	with open(pathfinder('tables/materials.csv')) as mats: # Precious materials
		materials = mats.readlines()
		materials = [mat.rstrip("\n") for mat in materials]

	loot = pd.read_csv(input_file, names=["Name", "Amount"]) # User-defined loot

	# Clean data
	table["Name"] = table["Name"].apply(lambda name : name.lower()) # Make all names lowercase
	runes["Name"] = runes["Name"].apply(lambda name : name.lower())
	loot["Name"] = loot["Name"].apply(lambda name : name.lower())

	rune_names["Replacer"].fillna("", inplace=True) # Fill NaN values with empty strings

	loot["Amount"].fillna(1, inplace=True) # Assume no amount means 1
	loot["Amount"].replace("\D", 0, regex=True, inplace=True) # Uses regex to replace non-numeric values in the "Amount" column
	loot["Amount"] = loot["Amount"].astype(int)


	money = {
		"item": Money(),
		"currency": Money(origin="currency")
	}


	# Get the price for each item
	for _, row in loot.iterrows():
		if "+1" in row["Name"] or "+2" in row["Name"] or "+3" in row["Name"]: # Check if there is a fundamental rune in the item
			temp_money = rune_calculator(row.tolist()[0], row.tolist()[1], table, runes, rune_names, materials)
			money[temp_money.origin] += temp_money
		else:
			temp_money = parse_database(row.tolist()[0], row.tolist()[1], table, materials)
			money[temp_money.origin] += temp_money

	if level is None:
		# If no level is passed, ask for it interactively
		while True:
			try:
				level = input("Enter the party's level or a range of levels (e.g. 5-8): ")
				split = level.split("-")
				if [level] == split:
					level = int(level)
					level_range = False
				else:
					level = [int(x) for x in split]
					level_range = True

			except ValueError:
				print("Please only insert an integer or a range with the syntax X-Y.")

			else:
				if level_range:
					if 0 < level[0] <= 20 and 0 < level[1] <= 20:
						total_value = tbl["Total Value"][min(level)-1:max(level)-1].sum() # Get total value from the TBL table
						break
					else:
						print("Please only insert levels between 1 and 20")
				else:
					if 0 < level <= 20:
						total_value = tbl.at[level - 1, "Total Value"] # Get total value from the TBL table
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
		for elem in split:
			try: int(elem)
			except ValueError:
				print("Invalid level type.\nPlease only insert an integer or a range with the syntax X-Y.")
				sys.exit(1)

		if [level] == split:
			level = int(level)
			level_range = False
		else:
			level = [int(x) for x in split]
			level_range = True

		if level_range:
			if 0 < level[0] <= 20 and 0 < level[1] <= 20:
				total_value = tbl["Total Value"][min(level)-1:max(level)-1].sum() # Get total value from the TBL table
			else:
				print("Please only insert levels between 1 and 20")
				sys.exit(1)
		else:
			if 0 < level <= 20:
				total_value = tbl.at[level - 1, "Total Value"] # Get total value from the TBL table
			else:
				print("Please only insert a level between 1 and 20")
				sys.exit(1)

	money["currency"] += Money(gp=currency, origin="currency")
	# if currency is None:
	# 	choice = input("Do you want to add extra currency (in gp)? (y/[n]) ") # Ask to add extra plain currency
	# 	if choice == "y":
	# 		while True:
	# 			try:
	# 				currency = int(input("How much? "))
	# 			except ValueError:
	# 				print("Please only insert an integer")
	# 			else:
	# 				if currency < 0:
	# 					print("Please only insert a positive number")
	# 				else:
	# 					money["currency"].gp += currency
	# 					break
	# 	else:
	# 		currency = 0

	# Convert coins in gp where possible
	for origin in money.keys():
		money[origin].gp += int(money[origin].cp/100)
		money[origin].gp += int(money[origin].sp/10)
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
		print(f"{abs(total_value - money['total'].gp)} gp too much (Expected: {total_value} gp)")
	elif total_value - money["total"].gp > 0:
		print(f"{abs(total_value - money['total'].gp)} gp too little (Expected: {total_value} gp)")
	else:
		print(f"None (Expected: {total_value} gp)")

def entry_point():
	parser = argparse.ArgumentParser(description="A simple tool for Pathfinder 2e to calculate how much your loot is worth.")
	parser.add_argument("input", type=str, nargs='?', default='',
						help="the name of the text file containing the loot")
	parser.add_argument("-l", "--level", type=str,
						help="the level of the party; can be an integer or of the form X-Y (eg. 5-8)")
	parser.add_argument("-c", "--currency", type=int, default=0,
	 					help="a flat amount of gp to add to the total")
	parser.add_argument("-f", "--format", action="store_true",
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

if __name__ == "__main__":
	entry_point()


# TODO
# [DONE] Allow adding an arbitrary amount of gold for plain wealth
# [DONE] Check what happens if you add a comma but no quantity (i.e. tindertwig, )
# [DONE] Add support for dynamic rune price calculation (i.e. auto-calculate price of +1 striking keen warhammer). Maybe use that all items with runes must start with a +
# [DONE] Add support for calculating wealth only for a specific (range of) level(s), instead of all of them up to the user input
# Maybe change item_info type to dict or custom data structure
# Print how many items of a given level, category and rarity there are
# Add different verbosity levels
# Add support for multiple file input, which calculates the value of all of the items in every file. Useful, for instance, to keep loot for each level or area separate
# Add description of how levels/level ranges work in the help description
# Add switch to autocorrect spelling mistakes instead of just suggest corrections
# Make amount columns optional (default is 1)
# Add platinum piece support?

# Known exceptions:
# Handwraps of mighty blows don't have a listing in the item list without runes: add special warning about that
# Wands and scrolls don't have a listing, however their naming scheme is standardized so they can be automated
# Add dragon's breath rune and called rune handling