import pandas as pd
import re
from difflib import get_close_matches

def parse_database(item, price, df: pd.DataFrame):
    """Parses the passed DataFrame and fetches the item's price."""
    
    item_row = df[df["Name"] == item[0].strip()]

    # If there is no item with the give name, find closest item to suggest and print a warning
    if item_row.empty == True:
        suggestion = "".join(get_close_matches(item[0].strip(), df["Name"].tolist(), 1, 0))
        print(f'WARNING: Item "{item[0]}" was not found in the database. Did you mean "{suggestion}"?')
        return

    # Add item price to the total
    add_price(item_row["Price"].item(), item[1], price)

def rune_calculator(item, price, df: pd.DataFrame, runelist: pd.DataFrame, rune_names: pd.DataFrame):
    """Automatically breaks down the item's name into singular runes and adds the price of each singularly."""

    item_runes = item[0].split() # Break up the name into single runes
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
        match rune:
            case "greater":
                rune = item_runes[cur_index + 1] + " (greater)"
                del item_runes[cur_index + 1]
            case "major":
                rune = item_runes[cur_index + 1] + " (major)"
                del item_runes[cur_index + 1]
            case "true":
                rune = item_runes[cur_index + 1] + " (true)"
                del item_runes[cur_index + 1]
            case "lesser":
                rune = item_runes[cur_index + 1] + " (lesser)"
                del item_runes[cur_index + 1]
            case "moderate":
                rune = item_runes[cur_index + 1] + " (moderate)"
                del item_runes[cur_index + 1]

        # Check if the name needs to be replaced
        rune_row = rune_names[rune_names["Name"] == rune]
        if rune_row.empty == False:
            rune = rune_row["Replacer"].item()
            if rune == "":
                continue
        
        # Find the rune in the list of runes (if present)
        item_row = runelist[runelist["Name"] == rune]

        # If it's not in the list of runes, check if it's another item
        if item_row.empty == True:
            item_row = df[df["Name"] == rune]

        # If it's again not in the list, it might just be a multi-word item name
        # It's guaranteed to not be a rune as it already checked in the rune list
        if item_row.empty == True:
            new_rune = rune # Preserves original rune name to allow for proper error messages
            increment = 1

            while True:
                try:
                    new_rune += " " + item_runes[cur_index + increment] # Iteratively append the following runes in the item name until it finds something
                    item_row = df[df["Name"] == new_rune]
                    if item_row.empty == False: # If it finds something, continue with price calculation and finish loop
                        breaker = True # Non-rune items must always be at the end of the name, thus it's guaranteed there's nothing left
                        break
                    increment += 1

                except IndexError: # If it can't find anything, stop execution and return -1
                    return -1
        
        # If it is still not on the list, warn the user and skip the current item
        if item_row.empty == True and rune != "":
            print(f'WARNING: Rune "{rune}" was not found in the database. Skipping rest of item.')
            continue
        
        # Use the cached fundamental rune to add the appropriate price, depending on category
        if item_row["Category"].item() == "Weapons":
            match rune_queue:
                case "+1": price["gp"] += 35
                case "+2": price["gp"] += 935
                case "+3": price["gp"] += 8935
            del rune_queue

        if item_row["Category"].item() == "Armor":
            match rune_queue:
                case "+1": price["gp"] += 160
                case "+2": price["gp"] += 1060
                case "+3": price["gp"] += 20560
            del rune_queue

        # Add item price to the total
        add_price(item_row["Price"].item(), item[1], price)

        if breaker:
            break

def add_price(price_str: str, amount: int, price_dict: dict):
    """Adds the price of the given item to the given price dictionary.\n
       item_row is a string that includes the price and coin type (i.e. 12 gp).\n
       amount is an integer that multiplies the price of the given item before adding it.\n
       price_dict is a dictionary that contains integer values for keys \"cp\", \"sp\" and \"gp\"."""

    # Fetch price and coin type through regex
    item_price = (re.search("\d*(,\d*)?", price_str)).group()
    coin_type = re.search("cp|sp|gp", price_str)

    # Check which kind of coin it is (if any)
    if coin_type is not None:
        match coin_type.group():
            case "cp": price_dict["cp"] += int(re.sub(",", "", item_price)) * amount # Add to total while multiplying by quantity
            case "sp": price_dict["sp"] += int(re.sub(",", "", item_price)) * amount # Regex is totally unnecessary but might as well
            case "gp": price_dict["gp"] += int(re.sub(",", "", item_price)) * amount


# Read the necessary files
table = pd.read_csv('PF2eItemList.csv', dtype={'Level': int}) # List of all items
runes = pd.read_csv('runes.csv') # List of just runes
rune_names = pd.read_csv('rune_names.csv') # Rune name translation table
tbl = pd.read_csv('treasurebylevel.csv') # Treasure by level table

loot = pd.read_csv('loot.txt', names=["Name", "Amount"]) # User-defined loot

# Clean data
table["Name"] = table["Name"].apply(lambda name : name.lower()) # Make all names lowercase
runes["Name"] = runes["Name"].apply(lambda name : name.lower())
loot["Name"] = loot["Name"].apply(lambda name : name.lower())

rune_names["Replacer"].fillna("", inplace=True) # Fill NaN values with empty strings

loot["Amount"].fillna(1, inplace=True) # Assume no amount means 1
loot["Amount"].replace("\D", 0, regex=True, inplace=True) # Uses regex to replace non-numeric values in the "Amount" column
loot["Amount"] = loot["Amount"].astype(int)

price = {
    "cp":  0,
    "sp":  0,
    "gp":  0
}

# Get the price for each item
for index, row in loot.iterrows():
    if "+1" in row["Name"] or "+2" in row["Name"] or "+3" in row["Name"]: # Check if there is a fundamental rune in the item
        rune_calculator(row.tolist(), price, table, runes, rune_names)
    else:
        parse_database(row.tolist(), price, table)

while True: # Ask for the party level
    try:
        level = int(input("Enter the party's level: "))
    except:
        print("Please only insert an integer")
    else:
        if level > 0 and level <= 20:
            break
        else:
            print("Please only insert a level between 1 and 20")

total_value = tbl.at[level - 1, "Total Value"] # Get total value from the TBL table

choice = input("Do you want to add extra currency (in gp)? (y/[n]) ") # Ask to add extra plain currency
if choice == "y":
    while True:
        try:
            currency = int(input("How much? "))
        except:
            print("Please only insert an integer")
        else:
            if currency < 0:
                print("Please only insert a positive number")
            else:
                price["gp"] += currency
                break
else:
    currency = 0

# Convert coins in gp where possible
price["gp"] += int(price["cp"]/100)
price["gp"] += int(price["sp"]/10)
price["cp"] %= 100
price["sp"] %= 10

print("\nTotal price (converted in gp):")
print(str(price["cp"]) + " cp")
print(str(price["sp"]) + " sp")
print(str(price["gp"] + currency) + " gp\n")

# print("Expected wealth for the party's level:")
# print(str(total_value) + " gp\n")

print("Difference:")
if total_value - price["gp"] < 0:
    print(f"{abs(total_value - price['gp'])} gp too much (Expected: {total_value} gp)")
elif total_value - price["gp"] > 0:
    print(f"{abs(total_value - price['gp'])} gp too little (Expected: {total_value} gp)")
else:
    print("None")

# TODO
# [DONE] Allow adding an arbitrary amount of gold for plain wealth
# [DONE] Check what happens if you add a comma but no quantity (i.e. tindertwig, )
# [DONE] Add support for dynamic rune price calculation (i.e. auto-calculate price of +1 striking keen warhammer). Maybe use that all items with runes must start with a +
# Add support for calculating wealth only for a specific (range of) level(s), instead of all of them up to the user input
# Include cp and sp in difference calculation
# Print the how many items of a given level, category and rarity there are

# Known exceptions:
# Handwraps of mighty blows doesn't have a listing in the item list without runes: add special warning about that
# Wands and scrolls don't have a listing, however their naming scheme is standardized so they can be automated
# Add dragon's breath rune and called rune handling