import pandas as pd
import re
from difflib import get_close_matches
from dataclasses import dataclass

@dataclass
class Money:
	"""
	Simple data structure for cp/sp/gp amounts.
	"""
	cp: int = 0
	sp: int = 0
	gp: int = 0

	def __add__(self, val):
		if type(val) == int:
			return Money(self.cp + val, self.sp + val, self.gp + val)
		elif type(val) == Money:
			return Money(self.cp + val.cp, self.sp + val.sp, self.gp + val.gp)
		else:
			raise TypeError(f"Unsupported sum operation for type {type(val)} on class Money")

def parse_database(item_name: str, amount: int, df: pd.DataFrame, materials: list, *,
				   return_cat: bool=False) -> Money:
	"""Parses the passed DataFrame and returns the item's price."""
	material = False

	# Check if the first one or two words denote a precious material
	name_list = item_name.split(" ")
	if name_list[0] in materials:
		# print(f"Found {name_list[0]} in the list.")
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
				# print(f"Found {name_list[0]} {name_list[1]} in the list.")
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
		suggestion = "".join(get_close_matches(item_name.strip(), df["Name"].tolist(), 1, 0))
		print(f'WARNING: Item "{item_name}" was not found in the database. Did you mean "{suggestion}"?')
		return Money()

	item_category = item_row["Category"].item()
	# Add item price to the total
	if not material:
		if return_cat:
			return (get_price(item_row["Price"].item(), amount), item_category)
		else:
			return get_price(item_row["Price"].item(), amount)
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
		price = get_price(df[df["Name"] == f"{material} {categories[item_category]} {grade}"]["Price"].item(), amount)

		# Add the price of the base item
		price += get_price(item_row["Price"].item(), amount)

		if return_cat:
			return (price, item_category)
		else:
			return price

def rune_calculator(item_name, amount, df: pd.DataFrame, runelist: pd.DataFrame, rune_names: pd.DataFrame,
					materials: pd.DataFrame) -> Money:
	"""Automatically breaks down the item's name into singular runes and returns the total price as a Money object."""

	# Helper function to make fundamental rune handling easier
	def get_cached_rune_price(cached_rune: str, category: str) -> Money:
		"Use the cached fundamental rune to add the appropriate price, depending on category"

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
	rune_queue = "0"
	cur_index = 0
	breaker = False

	# Cycle through runes found in the item name
	for cur_index, rune in enumerate(item_runes):
		rune = rune.strip()

		# Find fundamental rune and keep it in queue
		if rune == "+1":
			rune_queue = "+1"
			continue
		elif rune == "+2":
			rune_queue = "+2"
			continue
		elif rune == "+3":
			rune_queue = "+3"
			continue

		# Handle rune prefixes manually
		if rune in ("lesser", "moderate", "greater", "major", "true"):
			rune = f"{item_runes[cur_index + 1]} ({rune})"
			del item_runes[cur_index + 1]

		# match rune:
		#     case "greater":
		#         rune = item_runes[cur_index + 1] + " (greater)"
		#         del item_runes[cur_index + 1]
		#     case "major":
		#         rune = item_runes[cur_index + 1] + " (major)"
		#         del item_runes[cur_index + 1]
		#     case "true":
		#         rune = item_runes[cur_index + 1] + " (true)"
		#         del item_runes[cur_index + 1]
		#     case "lesser":
		#         rune = item_runes[cur_index + 1] + " (lesser)"
		#         del item_runes[cur_index + 1]
		#     case "moderate":
		#         rune = item_runes[cur_index + 1] + " (moderate)"
		#         del item_runes[cur_index + 1]

		# Check if the name needs to be replaced
		rune_row = rune_names[rune_names["Name"] == rune]
		if not rune_row.empty:
			rune = rune_row["Replacer"].item()
			if rune == "":
				continue

		# Find the rune in the list of runes (if present)
		item_row = runelist[runelist["Name"] == rune]

		# If it's not in the list of runes, check if it's another item
		if item_row.empty:
			item_row = df[df["Name"] == rune]

		# If it's again not in the list, it might just be a multi-word item name or a precious material
		# It's guaranteed to not be a rune as it already checked in the rune list
		if item_row.empty:
			new_rune = rune # Preserves original rune name to allow for proper error messages
			increment = 1

			while True:
				try:
					new_rune += " " + item_runes[cur_index + increment] # Iteratively append the following runes in the item name until it finds something
					item_row = df[df["Name"] == new_rune]
					if not item_row.empty: # If it finds something, continue with price calculation and finish loop
						breaker = True # Non-rune items must always be at the end of the name, thus it's guaranteed there's nothing left
						break
					increment += 1

				# Once nothing is left, check database if it can find the item
				# This is necessary to handle precious materials
				except IndexError:
					price, item_category = parse_database(new_rune, amount, df, materials, return_cat=True)
					if price == Money():
						print(f"WARNING: No results for {item_name}. Skipping price calculation.")
						return Money()
					else:
						running_sum += price
						running_sum += get_cached_rune_price(rune_queue, item_category)
						return running_sum

		# Add fundamental rune price and base item price to the total
		running_sum += get_cached_rune_price(rune_queue, item_row["Category"].item())
		running_sum += get_price(item_row["Price"].item(), amount)

		if breaker:
			break

	return running_sum

def get_price(price_str: str, amount: int, *, money: Money=None) -> Money | None:
	"""
	Gets the price of the given item and optionally adds it to the given Money object.

	item_row is a string that includes the price and coin type (i.e. 12 gp).

	amount is an integer that multiplies the price of the given item before adding it.

	price_dict is a Money object.
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



if __name__ == "__main__":
	# Read the necessary files
	table = pd.read_csv('./files/PF2eItemList.csv', dtype={'Level': int}) # List of all items
	runes = pd.read_csv('./files/runes.csv') # List of just runes
	rune_names = pd.read_csv('./files/rune_names.csv') # Rune name translation table
	tbl = pd.read_csv('./files/treasurebylevel.csv') # Treasure by level table
	with open('./files/materials.csv') as mats: # Precious materials
		materials = mats.readlines()
		materials = [mat.rstrip("\n") for mat in materials]

	loot = pd.read_csv('loot.txt', names=["Name", "Amount"]) # User-defined loot

	# Clean data
	table["Name"] = table["Name"].apply(lambda name : name.lower()) # Make all names lowercase
	runes["Name"] = runes["Name"].apply(lambda name : name.lower())
	loot["Name"] = loot["Name"].apply(lambda name : name.lower())

	rune_names["Replacer"].fillna("", inplace=True) # Fill NaN values with empty strings

	loot["Amount"].fillna(1, inplace=True) # Assume no amount means 1
	loot["Amount"].replace("\D", 0, regex=True, inplace=True) # Uses regex to replace non-numeric values in the "Amount" column
	loot["Amount"] = loot["Amount"].astype(int)

	money = Money()



	# Get the price for each item
	for index, row in loot.iterrows():
		if "+1" in row["Name"] or "+2" in row["Name"] or "+3" in row["Name"]: # Check if there is a fundamental rune in the item
			money += rune_calculator(row.tolist()[0], row.tolist()[1], table, runes, rune_names, materials)
		else:
			money += parse_database(row.tolist()[0], row.tolist()[1], table, materials)

	while True: # Ask for the party level
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


	choice = input("Do you want to add extra currency (in gp)? (y/[n]) ") # Ask to add extra plain currency
	if choice == "y":
		while True:
			try:
				currency = int(input("How much? "))
			except ValueError:
				print("Please only insert an integer")
			else:
				if currency < 0:
					print("Please only insert a positive number")
				else:
					money.gp += currency
					break
	else:
		currency = 0

	# Convert coins in gp where possible
	money.gp += int(money.cp/100)
	money.gp += int(money.sp/10)
	money.cp %= 100
	money.sp %= 10

	print(f"""
Total value (converted in gp):
	{str(money.cp)} cp
	{str(money.sp)} sp
	{str(money.gp)} gp

Of which:
	Items: {money.gp - currency} gp
	Currency: {currency} gp
""")

	print("Difference:")
	if total_value - money.gp < 0:
		print(f"{abs(total_value - money.gp)} gp too much (Expected: {total_value} gp)")
	elif total_value - money.gp > 0:
		print(f"{abs(total_value - money.gp)} gp too little (Expected: {total_value} gp)")
	else:
		print("None")

# TODO
# [DONE] Allow adding an arbitrary amount of gold for plain wealth
# [DONE] Check what happens if you add a comma but no quantity (i.e. tindertwig, )
# [DONE] Add support for dynamic rune price calculation (i.e. auto-calculate price of +1 striking keen warhammer). Maybe use that all items with runes must start with a +
# [DONE] Add support for calculating wealth only for a specific (range of) level(s), instead of all of them up to the user input
# Print how many items of a given level, category and rarity there are

# Known exceptions:
# Handwraps of mighty blows don't have a listing in the item list without runes: add special warning about that
# Wands and scrolls don't have a listing, however their naming scheme is standardized so they can be automated
# Add dragon's breath rune and called rune handling