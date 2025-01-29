import json
from general import merge_dicts

def adapt_state_data(data):
    """
    takes state data and refactors it for the reels, coins, and landlord hp
    """
    data["reels"] = [None, None, None, None, None]
    pop_keys = []
    for key in data:
        if key.startswith("Reel"):
            reel_num = 0
            if key != "Reel":
                reel_num = int(key[-1]) - 1
            data["reels"][reel_num] = data[key]
            pop_keys.append(key)
    for key in pop_keys:
        data.pop(key)

    if (data.get("coins") and data.get("coin_increase")):
        data["coins"] += data["coin_increase"]
    
    if (data.get("landlord_hp") and data.get("hp_decrease")):
        data["landlord_hp"] -= data["hp_decrease"]
    
    return data

def analyze_save(data):
    """
    takes a save file line and returns sections of parsed data
    """
    cur_path: str = data["path"].split("/")[-1]
    return_data = {}
    symbols = []

    try:
        if cur_path.startswith("Reel"):
            for i in range(len(data["icon_types"])):
                symbol = data["icon_types"][i]

                if data["saved_icon_data"][0] != None:
                    symbol_data = data["saved_icon_data"][i]
                    if symbol != "empty":
                        da_symbol = {}
                        da_symbol["name"] = symbol
                        da_symbol["coins_earned"] = symbol_data["coins_earned"]
                        da_symbol["permanent_bonus"] = symbol_data["permanent_bonus"]
                        if symbol_data.get("permanent_multiplier"):
                            da_symbol["permanent_multiplier"] = symbol_data["permanent_multiplier"]
                        da_symbol["saved_value"] = symbol_data["saved_value"]

                        symbols.append(da_symbol)
            
            while len(data["icon_types"]) > data["max_icons"] - 1:
                data["icon_types"].pop()
            return_data[cur_path] = data["icon_types"]

        elif cur_path == "Coins":
            # coin count
            if (data.get("coins")):
                return_data["coins"] = data["coins"] + data["queued_increase"]
        
        elif cur_path == "Coin Sum":
            # coins again lol
            if (data.get("value")):
                if (data.get("adding")):
                    return_data["coin_increase"] = data["value"]

        elif cur_path == "Items":
            items = []
            item_count = 0

            for i in range(len(data["item_types"])):
                da_item = {}
                da_item["name"] = data["item_types"][i]
                da_item["count"] = data["item_count_data"][i]
                da_item["data"] = data["saved_item_data"][i]
                item_count += data["item_count_data"][i]
                items.append(da_item)
            
            # items
            return_data["items"] = items
            
            # item count
            return_data["item_count"] = item_count

            # destroyed items
            return_data["destroyed_items"] = data["destroyed_item_types"]
            
            # just added items
            if (len(data["just_added_items"]) > 0):
                return_data["just_added_items"] = data["just_added_items"]

        elif cur_path == "Pop-up":
            # token count
            return_data["removal_tokens"] = data["removal_tokens"]
            return_data["reroll_tokens"] = data["reroll_tokens"]
            return_data["essence_tokens"] = data["essence_tokens"]

            return_data["destroyed_symbols"] = data["destroyed_symbol_types"]
            return_data["removed_symbols"] = data["removed_symbol_types"]

            return_data["spins"] = data["spins"]
            return_data["floor"] = data["current_floor"]
            return_data["rent_value"] = data["rent_values"][0]

            return_data["endless"] = data["endless_mode"]

            # email text (including when there are >3 things to choose from)
            return_data["emails"] = None
            if (len(data["emails"]) > 0):
                return_data["emails"] = data["emails"]

            # things to choose from (symbols, items, essences)
            if (len(data["saved_card_types"]) > 0):
                return_data["saved_card_types"] = data["saved_card_types"]
            
            return_data["comfy_pillow_triggered"] = data["comfy_pillow_essence_triggers"] > 0 or data["comfy_pillow_triggers"] > 0

        elif cur_path == "Landlord":
            return_data["landlord_hp"] = data["hp"] - data["queued_damage"]
        
        elif cur_path == "HP Sum":
            # hp again lol
            if (data.get("hp_value")):
                if (data.get("adding")):
                    return_data["hp_decrease"] = data["hp_value"]

    except Exception as e:
        print(f"Error analyzing data: {e}")
    
    return_data["symbols"] = symbols
    return return_data

def analyze_file(file_path, print_save_data = False):
    """
    takes a save file, splits it by line, and parses each line as a json
    returns a single dictionary with all the data we need
    """
    state_data = {}

    with open(file_path, 'r') as file:
        try:
            for line in file:
                try:
                    data = json.loads(line)

                    if data:
                        file_data = json.dumps(data, indent=4)

                        if (data.get("path") and print_save_data):
                            data_path = data["path"].split("/")

                            with open(f"{data_path[-1]}.json", 'w') as f:
                                f.write(file_data)

                        state_data = merge_dicts(state_data, analyze_save(data))

                except json.JSONDecodeError as e:
                    pass
                    # print(f"Error decoding JSON line: {e}")

            state_data = adapt_state_data(state_data)

            return state_data
        except Exception as e:
            print(f"Error reading file: {e}")
            return state_data

def analyze_string(string_data, print_save_data = False):
    """
    analyze_file but for a string
    """
    state_data = {}

    for line in string_data.split("\n"):
        try:
            data = json.loads(line)

            if data:
                file_data = json.dumps(data, indent=4)

                if (data.get("path") and print_save_data):
                    data_path = data["path"].split("/")

                    with open(f"{data_path[-1]}.json", 'w') as f:
                        f.write(file_data)

                state_data = merge_dicts(state_data, analyze_save(data))

        except json.JSONDecodeError as e:
            pass
            # print(f"Error decoding JSON line: {e}")

    state_data = adapt_state_data(state_data)

    return state_data

def get_cut_file(file_path):
    """get rid of the things we don't want lol"""
    return_string = ""
    reject_line = ["Extra Sum"]

    with open(file_path, 'r') as file:
        try:
            for line in file:
                try:
                    data = json.loads(line)

                    if data:
                        if (data.get("path")):
                            data_path = data["path"].split("/")
                            if data_path[-1] in reject_line:
                                continue
                            return_string += line
                except json.JSONDecodeError as e:
                    pass
                    # print(f"Error decoding JSON line: {e}")
                    return ""
        except Exception as e:
            print(f"Error cutting file: {e}")

    return return_string
