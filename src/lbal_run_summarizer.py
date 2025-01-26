import random
import os
import json
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from collections import Counter
import math
from pathlib import Path
import platform

# WHAT IS A SPIN ?
# lets say a spin starts when the user presses the spacebar
# this will be used to determine unique things that make up a save
# so we can define a spin in terms of saves

# hey trampoline tales i know you're reading this
# add the direction arrows point to the save file i want to add an "arrows missed" stat
# also your game is awesome

class Bonus:
    """
    This is the class for the bonus stats in the fourth quadrant of a run summary
    """
    def __init__(self, entry_string, value = 0, reverse = False, threshold = 1, is_filler = False):
        self.entry_string = entry_string
        self.value = value
        self.reverse = reverse
        self.threshold = threshold
        self.is_filler = is_filler

class Struct:
    """
    turns dictionaries into objects
    """
    def __init__(self, **entries):
        self.__dict__.update(entries)

def get_resource_path(relative_path):
    """
    get the absolute path to a resource file
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def merge_dicts(*dicts):
    """
    merges two dictionaries, and merges the arrays nested inside
    """
    result = {}
    for dictionary in dicts:
        for key in dictionary:
            if key in result:
                if isinstance(result[key], list):
                    result[key].extend(dictionary[key])
                else:
                    result[key] = dictionary[key]
            else:
                result[key] = dictionary[key]
    return result

def determine_game_state(data, spins = 0, rent = 0, previous_game_state = "unknown", has_won = False):
    """
    determines the game state from parsed data
    if there is no data, the state is broken
    if the state is undeterminable anyways, the state is unknown
    """

    try:
        game_state = "unknown"
        if not data or len(data) == 0:
            return "broken"

        if (data.get("rent_value")):
            if (data["rent_value"] != rent):
                game_state = "increase_rent"

        if (data.get("spins")):
            if (data["spins"] != spins):
                game_state = "spun"
            
        if (game_state != "increase_rent" and game_state != "spun"):
            if data.get("emails"):
                if (len(data["emails"]) > 0):
                    if (data["emails"][0]["type"] == "add_tile"):
                        game_state = "add_symbol"
                    elif (data["emails"][0]["type"] == "add_item"):
                        game_state = "add_item"
                    elif (data["emails"][0]["type"] == "rent_due"):
                        game_state = "rent_due"
                    elif (data["emails"][0]["type"] == "init_comrade_help"):
                        game_state = "init_comrade_help"
                    elif (data["emails"][0]["type"] == "comrade_help"):
                        game_state = "comrade_help"
                    elif (data["emails"][0]["type"] == "swap_prompt_1"):
                        game_state = "swapping_device"
                    elif (data["emails"][0]["type"] == "oil_can_prompt"):
                        game_state = "oil_can"
                    elif (data["emails"][0]["type"] == "rent_increase") and game_state != "increase_rent":
                        game_state = "rent_increase"
                    elif (data["emails"][0]["type"] == "removal_token_prompt"):
                        game_state = "pre_spin"
                    elif (data["emails"][0]["type"] == "fine_print"):
                        game_state = "fine_print"
                    elif (data["emails"][0]["type"] == "game_over"):
                        game_state = "game_over"
                    elif (data["emails"][0]["type"] == "boss_fight_1"):
                        game_state = "pre_boss_landlord"
                    elif (data["emails"][0]["type"] == "boss_fight_2"):
                        game_state = "pre_boss_comrade"
                    elif (data["emails"][0]["type"] == "comfy_pillow_prompt"):
                        game_state = "comfy_pillow_prompt"
                    elif (data["emails"][0]["type"] == "comfy_pillow_essence_prompt"):
                        game_state = "comfy_pillow_essence_prompt"
                    elif (data["emails"][0]["type"] == "chili_powder_essence_prompt"):
                        game_state = "chili_powder_essence"
                else:
                    game_state = "pre_spin"
            else:
                game_state = "pre_spin"
        
        if not has_won and data["landlord_hp"] <= 0 and game_state != "pre_spin" and previous_game_state != "win":
            game_state = "win"
        
        if data.get("coins"):
            if data["coins"] >= 1000000000 and data["endless"] and any(item["name"] == "guillotine_essence" for item in data["items"]):
                game_state = "guillotined"

        return game_state
    except Exception as e:
        print(f"Error determining game state: {e}")
        return "unknown"

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
                        if da_symbol.get("permanent_multiplier"):
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

def add_line_to_string(string = ""):
    return string + "\n"

def get_run_summary(run):
    """
    takes a run and returns 5 strings for a run summary
    """
    return_dict = {}
    return_dict["title"] = ""
    return_dict["general"] = ""
    return_dict["symbols"] = ""
    return_dict["items"] = ""
    return_dict["bonus"] = ""

    try:
        return_dict["title"] += add_line_to_string("Most recent run summary: ")

        if (run.game_state == "win"):
            return_dict["title"] += add_line_to_string("Victory!")
        
        if (run.game_state == "game_over"):
            return_dict["title"] += add_line_to_string("Defeat...")

        if (run.game_state == "guillotined"):
            return_dict["title"] += add_line_to_string("Executed by guillotine!")

        return_dict["general"] += add_line_to_string(f"Floor: {run.floor}")

        return_dict["general"] += add_line_to_string()

        # spin data--------------------------------------------
        return_dict["general"] += add_line_to_string(f"Spins: {run.spins}")
        return_dict["general"] += add_line_to_string(f"Best Spin by Coin Count: Spin {run.best_spin} ({run.best_spin_coins:,.0f} coins)")
        if (run.game_state != "guillotined"):
            return_dict["general"] += add_line_to_string(f"Best Spin Relative to Rent: Spin {run.best_spin_percent} ({run.best_spin_percent_coins:,.0f} coins, {round(run.best_spin_percent_val * 100, 2)}% of rent)")

        return_dict["general"] += add_line_to_string()
        
        # coin data--------------------------------------------
        if (run.game_state != "guillotined"):
            return_dict["general"] += add_line_to_string(f"Coins: {run.coins:,.0f}")

        total_coins = run.coins
        for rent in run.rents_paid:
            total_coins += rent
        return_dict["general"] += add_line_to_string(f"Total Coins Earned: {total_coins:,.0f}")

        # token data---------------------------------------------
        return_dict["general"] += add_line_to_string(f"Reroll Tokens Used: {run.rerolls_used}")
        return_dict["general"] += add_line_to_string(f"Removal Tokens Used: {run.removals_used}")
        return_dict["general"] += add_line_to_string(f"Essence Tokens Used: {run.essence_tokens_used}")

        # symbol data--------------------------------------------
        return_dict["symbols"] += add_line_to_string(f"Symbol Count: {len(run.symbols)}")

        sorted_symbols = sorted(run.symbols, key = lambda symbol: symbol["coins_earned"])
            
        if len(sorted_symbols) > 0:
            symbol_names = [symbol["name"] for symbol in sorted_symbols]
            symbol_counter = Counter(symbol_names)
            common_symbols = symbol_counter.most_common(None)

            common_string = ""
            for symbol in common_symbols:
                common_string += symbol[0] + " " + str(symbol[1]) + " "
            return_dict["symbols"] += add_line_to_string(common_string)

            return_dict["symbols"] += add_line_to_string("MVP Symbols:")
            mvp_symbol_count = 3

            i = len(sorted_symbols) - 1
            symbol = sorted_symbols[i]
            
            while i > -1 and i > len(sorted_symbols) - mvp_symbol_count - 1:
                symbol = sorted_symbols[i]
                bonus_list = []
                if symbol["permanent_bonus"] > 0:
                    bonus_list.append("+" + str(symbol["permanent_bonus"]))
                if symbol.get("permanent_multiplier"):
                    if symbol["permanent_multiplier"] > 1:
                        bonus_list.append("x" + str(symbol["permanent_multiplier"]))

                bonus_string = ""
                if len(bonus_list) > 0:
                    bonus_string += "("
                    for bonus in bonus_list:
                        bonus_string += bonus + ", "
                    bonus_string = bonus_string[:-2]
                    bonus_string += ")"
                return_dict["symbols"] += add_line_to_string(f"- {symbol['name']} {bonus_string} - {symbol['coins_earned']:,.0f} coins")
                i -= 1
        
        return_dict["symbols"] += add_line_to_string(f"Added Symbol Count: {len(run.added_symbols)}")

        if len(run.added_symbols) > 0:
            symbol_names = [symbol_name for symbol_name in run.added_symbols]
            symbol_counter = Counter(symbol_names)
            common_symbols = symbol_counter.most_common(None)

            if (run.game_state != "guillotined"):
                common_string = ""
                for symbol in common_symbols:
                    common_string += symbol[0] + " " + str(symbol[1]) + " "
            
                return_dict["symbols"] += add_line_to_string(common_string)
            else:
                return_dict["symbols"] += add_line_to_string(f"Most Added Symbol: {common_symbols[0][0]} ({common_symbols[0][1]})")
        
        return_dict["symbols"] += add_line_to_string(f"Skips: {run.symbol_skips}")

        return_dict["symbols"] += add_line_to_string(f"Destroyed Symbol Count: {len(run.destroyed_symbols)}")

        if len(run.destroyed_symbols) > 0:
            symbol_names = [symbol_name for symbol_name in run.destroyed_symbols]
            symbol_counter = Counter(symbol_names)
            common_symbols = symbol_counter.most_common(None)
     
            if (run.game_state != "guillotined"):
                common_string = ""
                for symbol in common_symbols:
                    common_string += symbol[0] + " " + str(symbol[1]) + " "
                return_dict["symbols"] += add_line_to_string(common_string)
            else:
                return_dict["symbols"] += add_line_to_string(f"Most Destroyed Symbol: {common_symbols[0][0]} ({common_symbols[0][1]})")
        
        return_dict["symbols"] += add_line_to_string(f"Removed Symbol Count: {len(run.removed_symbols)}")

        if len(run.removed_symbols) > 0:
            symbol_names = [symbol_name for symbol_name in run.removed_symbols]
            symbol_counter = Counter(symbol_names)
            common_symbols = symbol_counter.most_common(None)

            if (run.game_state != "guillotined"):
                common_string = ""
                for symbol in common_symbols:
                    common_string += symbol[0] + " " + str(symbol[1]) + " "
                return_dict["symbols"] += add_line_to_string(common_string)
            else:
                return_dict["symbols"] += add_line_to_string(f"Most Removed Symbol: {common_symbols[0][0]} ({common_symbols[0][1]})")

        # item and essence data----------------------------------------------
        actual_items = []
        actual_essences = []

        for item in run.items:
            item_name: str = item["name"]

            if item_name.endswith("_d"):
                item_name = item_name[:-2]
                item["name"] = item_name
            
            if item_name.endswith("_essence"):
                actual_essences.append(item)
            else:
                actual_items.append(item)

        return_dict["items"] += add_line_to_string(f"Item Count: {len(actual_items)}")

        if (run.game_state != "guillotined"):
            item_string = ""
            if len(actual_items) > 0:
                for item in actual_items:
                    item_string += item["name"] + " " + str(item["count"]) + " "
                item_string = item_string[:-1]
            else:
                item_string = "none"
            return_dict["items"] += add_line_to_string(item_string)

        return_dict["items"] += add_line_to_string()

        return_dict["items"] += add_line_to_string(f"Essence Count: {len(actual_essences)}")

        if (run.game_state != "guillotined"):
            essence_string = ""
            if len(actual_essences) > 0:
                for item in actual_essences:
                    essence_string += item["name"] + " " + str(item["count"]) + " "
                essence_string = essence_string[:-1]
            else:
                essence_string = "none"
            return_dict["items"] += add_line_to_string(essence_string)

        return_dict["items"] += add_line_to_string()

        return_dict["items"] += add_line_to_string("Destroyed Items: " + str(len(run.destroyed_items)))
        
        if (run.game_state != "guillotined"):
            if len(run.destroyed_items) > 0:
                item_names = [item_name for item_name in run.destroyed_items]
                item_counter = Counter(item_names)
                common_items = item_counter.most_common(None)

                common_string = ""
                for item in common_items:
                    common_string += item[0] + " " + str(item[1]) + " "
                return_dict["items"] += add_line_to_string(common_string)

                return_dict["items"] += add_line_to_string()

        # bonus data---------------------------------------
        bonus_stats_shown = 7
        filler_stats_guaranteed = 1
        
        for item in run.items:
            if item["name"] == "fish_bowl":
                run.bonus["fish_in_bowl"] = Bonus("Goldfish in Fish Bowl", item["data"])
            if item["name"] == "piggy_bank":
                run.bonus["coins_in_piggy_bank"] = Bonus("Coins in Piggy Bank", round(item["data"] * 2.5))
            if item["name"] == "swear_jar":
                run.bonus["coins_in_swear_jar"] = Bonus("Coins in Swear Jar", item["data"] * 2)
        
        symbol_data = {}
        with open(get_resource_path(f"symbol_data.json"), 'r') as f:
            symbol_data = json.load(f)

        scalers = [symbol_name for symbol_name in symbol_data if "scaler" in symbol_data[symbol_name]["groups"]]
        fruits = [symbol_name for symbol_name in symbol_data if "fruit" in symbol_data[symbol_name]["groups"]]
        foods = [symbol_name for symbol_name in symbol_data if "food" in symbol_data[symbol_name]["groups"]]
        gems = [symbol_name for symbol_name in symbol_data if "gem" in symbol_data[symbol_name]["groups"]]
        humans = [symbol_name for symbol_name in symbol_data if "human" in symbol_data[symbol_name]["groups"]]
        animals = [symbol_name for symbol_name in symbol_data if "animal" in symbol_data[symbol_name]["groups"]]
        hexes = [symbol_name for symbol_name in symbol_data if "hex" in symbol_data[symbol_name]["groups"]]
        capsules = [symbol_name for symbol_name in symbol_data if "capsule" in symbol_data[symbol_name]["groups"]]
        voids = [symbol_name for symbol_name in symbol_data if "void" in symbol_data[symbol_name]["groups"]]

        keys_to_delete = ["fruits", "foods", "gems", "humans", "animals", "hexes", "humans_destroyed", "capsules_destroyed", "foods_destroyed", "voids_destroyed"]
        for key in keys_to_delete:
            if run.bonus.get(key):
                run.bonus.pop(key)
            
        biggest_scalar = None
        symbols_by_bonus = sorted(run.symbols, key = lambda symbol: symbol["permanent_bonus"], reverse=True)

        # biggest scalar and filler stats-----------------------------------------
        for symbol in symbols_by_bonus:
            if biggest_scalar == None:
                if symbol["name"] in scalers:
                    biggest_scalar = symbol
                    run.bonus["biggest_scaler"] = Bonus("Biggest Scaler", symbol["permanent_bonus"])
            
            if symbol["name"] in fruits:
                if not run.bonus.get("fruits"):
                    run.bonus["fruits"] = Bonus("Fruits", threshold=3, is_filler=True)
                run.bonus["fruits"].value += 1
            
            if symbol["name"] in foods:
                if not run.bonus.get("foods"):
                    run.bonus["foods"] = Bonus("Foods", threshold=5, is_filler=True)
                run.bonus["foods"].value += 1

            if symbol["name"] in gems:
                if not run.bonus.get("gems"):
                    run.bonus["gems"] = Bonus("Gems", threshold=3, is_filler=True)
                run.bonus["gems"].value += 1
            
            if symbol["name"] in humans:
                if not run.bonus.get("humans"):
                    run.bonus["humans"] = Bonus("Humans", threshold=3, is_filler=True)
                run.bonus["humans"].value += 1
            
            if symbol["name"] in animals:
                if not run.bonus.get("animals"):
                    run.bonus["animals"] = Bonus("Animals", threshold=3, is_filler=True)
                run.bonus["animals"].value += 1
            
            if symbol["name"] in hexes:
                if not run.bonus.get("hexes"):
                    run.bonus["hexes"] = Bonus("Hexes", threshold=2, is_filler=True)
                run.bonus["hexes"].value += 1
        
        # destroyed symbols--------------------------------------
        for symbol_name in run.destroyed_symbols:
            if symbol_name in humans:
                if not run.bonus.get("humans_destroyed"):
                    run.bonus["humans_destroyed"] = Bonus("Humans Killed", threshold=3)
                run.bonus["humans_destroyed"].value += 1
            
            if symbol_name in foods:
                if not run.bonus.get("foods_destroyed"):
                    run.bonus["foods_destroyed"] = Bonus("Food Symbols Eaten", threshold=3)
                run.bonus["foods_destroyed"].value += 1
            
            if symbol_name in capsules:
                if not run.bonus.get("capsules_destroyed"):
                    run.bonus["capsules_destroyed"] = Bonus("Capsules Opened", threshold=7)
                run.bonus["capsules_destroyed"].value += 1
            
            if symbol_name in voids:
                if not run.bonus.get("voids_destroyed"):
                    run.bonus["voids_destroyed"] = Bonus("Void Symbols Destroyed", threshold=5)
                run.bonus["voids_destroyed"].value += 1

        eligible_stats = []
        eligible_filler_stats = []
        for key in run.bonus:
            bonus_stat = run.bonus[key]
            if (not bonus_stat.reverse and bonus_stat.value >= bonus_stat.threshold) or (bonus_stat.reverse and bonus_stat.value <= bonus_stat.threshold):
                if bonus_stat.is_filler:
                    eligible_filler_stats.append(bonus_stat)
                else:
                    eligible_stats.append(bonus_stat)
        
        random.shuffle(eligible_stats)
        random.shuffle(eligible_filler_stats)
        bonus_lines = 0

        for i in range(min(bonus_stats_shown, len(eligible_stats) - filler_stats_guaranteed)):
            bonus_stat = eligible_stats[i]

            if (bonus_stat == run.bonus["biggest_scaler"]):
                return_dict["bonus"] += add_line_to_string(bonus_stat.entry_string + ": " + biggest_scalar["name"] + f" (+{biggest_scalar['permanent_bonus']:,.0f})")
            else:
                return_dict["bonus"] += add_line_to_string(bonus_stat.entry_string + ": " + str(bonus_stat.value))

            bonus_lines += 1
        
        while bonus_lines < bonus_stats_shown and len(eligible_filler_stats) > 0:
            bonus_stat = eligible_filler_stats.pop(0)
            return_dict["bonus"] += add_line_to_string(bonus_stat.entry_string + ": " + str(bonus_stat.value))
            bonus_lines += 1


    except Exception as e:
        print("Error generating run summary: " + str(e))

    return return_dict

class OutlinedLabel(QLabel):
    """
    qlabel but with an outline
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.w = 1 / 25
        self.mode = True
        self.setBrush(Qt.white)
        self.setPen(Qt.black)
        self.emoji_path = get_resource_path("img")
        self.cur_height = 0

    def scaledOutlineMode(self):
        return self.mode

    def setScaledOutlineMode(self, state):
        self.mode = state

    def outlineThickness(self):
        return self.w * self.font().pointSize() if self.mode else self.w

    def setOutlineThickness(self, value):
        self.w = value

    def setBrush(self, brush):
        if not isinstance(brush, QBrush):
            brush = QBrush(brush)
        self.brush = brush

    def setPen(self, pen):
        if not isinstance(pen, QPen):
            pen = QPen(pen)
        pen.setJoinStyle(Qt.RoundJoin)
        self.pen = pen

    def sizeHint(self):
        w = math.ceil(self.outlineThickness() * 2)
        return super().sizeHint() + QSize(w, w)

    def minimumSizeHint(self):
        w = math.ceil(self.outlineThickness() * 2)
        return super().minimumSizeHint() + QSize(w, w)

    def paintEvent(self, event):
        w = self.outlineThickness()
        rect = self.rect()
        metrics = QFontMetrics(self.font())
        text = self.text()
        max_width = rect.width() - 2 * w  # account for padding or outline thickness

        emoji_files = {f.stem: f for f in Path(self.emoji_path).glob("*.png")}

        raw_lines = text.split("\n")
        lines = []
        sep = 0.85
        emoji_resize = 0.8
        emoji_gap = 1.1
        emoji_size_init = metrics.height()
        emoji_size = int(emoji_size_init * emoji_resize)

        # line wrapping logic
        for raw_line in raw_lines:
            words = raw_line.split(" ")
            current_line = ""
            line_with_emojis = ""
            emoji_count = 0

            for word in words:
                emoji_word = word.replace(",", "")
                is_emoji = emoji_word in emoji_files

                if is_emoji:
                    emoji_count += 1
                else:
                    test_line = f"{current_line} {word}".strip()

                if metrics.horizontalAdvance(test_line) + (emoji_count * emoji_size_init * emoji_gap) > max_width:
                    if line_with_emojis:
                        lines.append(line_with_emojis)
                    
                    emoji_count = 0
                    if not is_emoji:
                        current_line = word
                    else:
                        emoji_count += 1
                        current_line = ""

                    line_with_emojis = word
                else:
                    if is_emoji:
                        line_with_emojis = line_with_emojis + " " + word
                    else:
                        line_with_emojis = line_with_emojis + " " + word
                        current_line = test_line

            if line_with_emojis:
                lines.append(line_with_emojis)

        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)

        y_offset = rect.top() + w
        total_text_height = len(lines) * metrics.height() * sep

        # shrink font if it's too fat
        font_step = 8
        while total_text_height > self.height() and self.font().pointSize() != 1:
            cur_font = self.font()
            new_font_size = max(self.font().pointSize() - font_step, 1)
            cur_font.setPointSize(new_font_size)
            self.setFont(cur_font)
            metrics = QFontMetrics(cur_font)
            total_text_height = len(lines) * metrics.height() * sep
            emoji_size_init = metrics.height()
            emoji_size = int(emoji_size_init * emoji_resize)

        thick_percent = 1 / 400
        self.setOutlineThickness(self.font().pointSize() * thick_percent)

        if self.alignment() & Qt.AlignTop:
            y_offset = rect.top() + w + metrics.ascent()
        elif self.alignment() & Qt.AlignBottom:
            y_offset = rect.bottom() - total_text_height + metrics.ascent()
        else:
            y_offset = rect.top() + (rect.height() - total_text_height) / 2 + metrics.ascent()

        path = QPainterPath()

        for i, line in enumerate(lines):
            y = y_offset + i * metrics.height() * sep
            x = rect.left() + w

            for word in line.split(" "):
                emoji_word = word.replace(",", "")
                if emoji_word in emoji_files:
                    # draw emoji woth nearest neighbor scaling
                    emoji_image = QPixmap(str(emoji_files[emoji_word]))
                    scaled_emoji = emoji_image.scaled(
                        emoji_size, emoji_size, Qt.KeepAspectRatio, Qt.FastTransformation
                    )
                    _x = int(x + emoji_size_init - emoji_size)
                    _y = int(y - metrics.ascent() + emoji_size_init - emoji_size)
                    qp.drawPixmap(_x, _y, scaled_emoji)
                    x += int(emoji_size_init * emoji_gap)
                else:
                    # add text to path for outlining and filling
                    path.addText(QPointF(x, y), self.font(), word)
                    x += metrics.horizontalAdvance(word) + metrics.horizontalAdvance(" ")

        # draw outline
        self.pen.setWidthF(w * 2)
        qp.setPen(self.pen)
        qp.strokePath(path, self.pen)

        # draw fill
        qp.fillPath(path, self.brush)

class FileMonitorThread(QThread):
    """
    monitors the save file for updates and prints the run summary when the game ends
    this is where the magic happens
    """
    file_updated = pyqtSignal(dict)  # signal to send updated file content to the gui

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.running = True
    
    def run(self):
        if not os.path.exists(self.file_path):
            print(f"Error: The file '{self.file_path}' does not exist.")
            return

        self.file_updated.emit({"title": "Currently running, start a run in Luck Be A Landlord"})
        last_modified_time = os.path.getmtime(self.file_path)
        has_run_loop = True
        restart_da_run = True
        saves = 0
        previous_save = None
        previous_cut_file = ""
        print_save_data = False # export save data to a file
        run_valid = False # only start the run summary process if the run starts at spin zero
        always_show_summary = False # show run summary at any save update, even if run is invalid
        show_reassurance = True # show the "we are scanning your file rn" text, disabled after showing it

        def restart_run():
            run = lambda: None
            run.game_state = "unknown"
            run.previous_game_state = "unknown"
            run.floor = 0
            run.has_won = False

            run.rent = 25
            run.rents_paid = []

            run.spins = 0
            run.best_spin = 0
            run.best_spin_coins = 0
            run.best_spin_percent = 0 # in spins from spin 0
            run.best_spin_percent_coins = 0 # in coins
            run.best_spin_percent_val = 0 # in percentage as coins earned / rent
            
            run.coins = 1

            run.rerolls_used = 0
            run.removals_used = 0
            run.essence_tokens_used = 0

            run.symbols = []
            run.added_symbols = []
            run.symbol_skips = 0
            run.destroyed_symbols = []
            run.removed_symbols = []

            run.items = []
            run.destroyed_items = []
            run.item_count = 0

            run.bonus = {}
            run.bonus["times_comfy_pillow"] = Bonus("Comfy Pillow Activations", threshold=3)
            run.bonus["times_oil_can"] = Bonus("Oil Can Respins", threshold=3)
            run.bonus["times_swapping_device"] = Bonus("Swapping Device Swaps", threshold=3)
            run.bonus["anchors_in_corner"] = Bonus("Anchors in the Corner", threshold=3)

            return run
        
        run = None
        if restart_da_run or not os.path.exists(f"parsed_save.json"):
            run = restart_run()
        else:
            with open(f"parsed_save.json", 'r') as f:
                run = json.load(f)
                run = Struct(**run)

        while self.running:
            try:
                current_modified_time = os.path.getmtime(self.file_path)

                if current_modified_time != last_modified_time or not has_run_loop:
                    try:
                        last_modified_time = current_modified_time
                        saves += 1
                        
                        cut_file = get_cut_file(self.file_path)
                        
                        if cut_file != previous_cut_file:
                            parsed_save = analyze_string(cut_file, print_save_data)

                            if not has_run_loop:
                                run.spins = parsed_save["spins"]
                                run.rent = parsed_save["rent_value"]
                                run.coins = parsed_save["coins"]

                            parsed_save["previous_game_state"] = run.previous_game_state

                            game_state = "broken"

                            if cut_file != "":
                                game_state = determine_game_state(parsed_save, run.spins, run.rent, run.previous_game_state, run.has_won)

                            try:
                                # game state if it didn't get changed to unknown
                                game_state_unconditional = game_state

                                if previous_save != None:
                                    if previous_save.get("game_state"):
                                        if game_state == previous_save["game_state"]:
                                            trimmed_previous_save = previous_save.copy()
                                            trimmed_previous_save.pop("previous_game_state")
                                            trimmed_previous_save.pop("game_state")

                                            trimmed_parsed_save = parsed_save.copy()
                                            trimmed_parsed_save.pop("previous_game_state")

                                            if trimmed_previous_save == trimmed_parsed_save:
                                                # duplicate saves can happen when things we don't care about are updated
                                                game_state = "broken"

                                if (game_state != "broken"):
                                    run.game_state = game_state

                                    if parsed_save["spins"] == 0:
                                        run = restart_run()
                                        if not always_show_summary and show_reassurance:
                                            self.file_updated.emit({"title": "Currently analyzing your game\nYou will see a run summary when the game is complete!"})
                                            show_reassurance = False
                                        run_valid = True

                                    if (parsed_save.get("symbols")):
                                        run.symbols = parsed_save["symbols"]
                                        run.destroyed_symbols = parsed_save["destroyed_symbols"]
                                        run.removed_symbols = parsed_save["removed_symbols"]
                                    
                                    if not run_valid and not always_show_summary:
                                        self.file_updated.emit({"title": "Waiting for a new game to start\n(cannot generate run summary from current game)"})
                                    
                                    if (game_state == "spun" or game_state == "win"):
                                        run.spins = parsed_save["spins"]

                                        if parsed_save.get("coins"):
                                            coins_earned_this_spin = parsed_save["coins"] - run.coins

                                            if (run.best_spin_coins < coins_earned_this_spin):
                                                run.best_spin = run.spins
                                                run.best_spin_coins = coins_earned_this_spin
                                            
                                            if run.rent != 0:
                                                if (run.best_spin_percent_val < coins_earned_this_spin / run.rent):
                                                    run.best_spin_percent = run.spins
                                                    run.best_spin_percent_coins = coins_earned_this_spin
                                                    run.best_spin_percent_val = coins_earned_this_spin / run.rent
                                        
                                        if parsed_save.get("reels"):
                                            if (parsed_save["reels"][0][0] == "anchor"):
                                                run.bonus["anchors_in_corner"].value += 1
                                            if (parsed_save["reels"][0][len(parsed_save["reels"][0]) - 1] == "anchor"):
                                                run.bonus["anchors_in_corner"].value += 1
                                            if (parsed_save["reels"][len(parsed_save["reels"]) - 1][0] == "anchor"):
                                                run.bonus["anchors_in_corner"].value += 1
                                            if (parsed_save["reels"][len(parsed_save["reels"]) - 1][len(parsed_save["reels"][len(parsed_save["reels"]) - 1]) - 1] == "anchor"):
                                                run.bonus["anchors_in_corner"].value += 1

                                    if run.previous_game_state == "add_symbol":
                                        if len(run.symbols) == len(previous_save["symbols"]):
                                            if (parsed_save["reroll_tokens"] < previous_save["reroll_tokens"]):
                                                run.rerolls_used += previous_save["reroll_tokens"] - parsed_save["reroll_tokens"]
                                            else:
                                                run.symbol_skips += 1
                                        else:
                                            current_symbol_names = [symbol["name"] for symbol in run.symbols]
                                            previous_symbol_names = [symbol["name"] for symbol in previous_save["symbols"]]
                                            for name in previous_symbol_names:
                                                if name in current_symbol_names:
                                                    current_symbol_names.pop(current_symbol_names.index(name))
                                            run.added_symbols.append(current_symbol_names[0])

                                    if parsed_save.get("coins"):
                                        run.coins = parsed_save["coins"]
                                    if parsed_save.get("items"):
                                        run.items = parsed_save["items"]
                                        run.item_count = parsed_save["item_count"]
                                        run.destroyed_items = parsed_save["destroyed_items"]
                                    if parsed_save.get("floor"):
                                        run.floor = parsed_save["floor"]
                                    
                                    if (game_state == "increase_rent"):
                                        run.rents_paid.append(run.rent)
                                        run.rent = parsed_save["rent_value"]
                                    
                                    if (game_state == "pre_spin"):
                                        if run.previous_game_state == "pre_spin":
                                            if (parsed_save["removal_tokens"] < previous_save["removal_tokens"]):
                                                run.removals_used += previous_save["removal_tokens"] - parsed_save["removal_tokens"]
                                        
                                        if run.previous_game_state == "oil_can":
                                            if parsed_save["reels"] != previous_save["reels"]:
                                                run.bonus["times_oil_can"].value += 1

                                        if run.previous_game_state == "swapping_device":
                                            if parsed_save["reels"] != previous_save["reels"]:
                                                run.bonus["times_swapping_device"].value += 1
                                    
                                    if (game_state == "win"):
                                        run.has_won = True
                                    
                                    if run.previous_game_state == "comfy_pillow_prompt" or run.previous_game_state == "comfy_pillow_essence_prompt":
                                        if parsed_save["comfy_pillow_triggered"] > 0:
                                            run.bonus["times_comfy_pillow"].value += 1
                                    
                                    if game_state == "add_item":
                                        if parsed_save["saved_card_types"][0].endswith("_essence"):
                                            run.essence_tokens_used += 1

                                    # show me useful stuff --------------------------------------------
                                    print(f"Spin {run.spins} {game_state}")
                                    
                                    if ((game_state == "win" or game_state == "game_over" or game_state == "guillotined") and run_valid) or (always_show_summary):
                                        self.file_updated.emit(get_run_summary(run))
                                    
                                    print()

                                    parsed_save["game_state"] = game_state_unconditional
                                    run.previous_game_state = game_state_unconditional
                                    previous_save = parsed_save
                                else:
                                    parsed_save["game_state"] = run.previous_game_state
                                    run.previous_game_state = run.previous_game_state

                                if print_save_data:
                                    with open(f"parsed_save.json", 'w') as f:
                                        json.dump(parsed_save, f, indent=4)
                            except Exception as e:
                                print(f"Error processing save: {e}")
                                print()

                            has_run_loop = True
                    
                        if (cut_file != ""):
                            previous_cut_file = cut_file
                    except Exception as e:
                        print(f"Error monitoring file: {e}")

            except Exception as e:
                print(f"Error: {e}")
                break
        
    def stop(self):
        self.running = False
        self.wait()

class FileMonitorApp(QWidget):
    """
    manages the window and the text and stuff
    """
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.init_ui()

        # start the file monitoring thread
        self.monitor_thread = FileMonitorThread(self.file_path)
        self.monitor_thread.file_updated.connect(self.update_text)
        self.monitor_thread.start()

    def update_positions(self):
        """
        update the positions of the textboxes
        ughhh this code sucks
        """
        grid_top = self.text_boxes["title"].height() + self.padding
        grid_width = self.width() - (2 * self.padding)
        grid_height = self.height() - grid_top - self.padding
        symbol_height_scale = 1.35

        # place the 2x2 textboxes dynamically
        box_width = grid_width // 2 - self.padding
        box_height = grid_height // 2 - self.padding

        positions = [
            (self.padding, grid_top),  # general
            (self.padding + box_width + self.padding, grid_top),  # symbols
            (self.padding, grid_top + box_height + self.padding),  # items
            (self.padding + box_width + self.padding, int(grid_top + box_height * symbol_height_scale + self.padding)),  # bonus
        ]

        for name in ["title", "general", "symbols", "items", "bonus"]:
            self.text_boxes[name].setFont(self.custom_font)

        for name, (x, y) in zip(["general", "symbols", "items", "bonus"], positions):
            if name == "symbols":
                self.text_boxes[name].setGeometry(x, y, box_width, int(box_height * symbol_height_scale))
            elif name == "bonus":
                self.text_boxes[name].setGeometry(x, y, box_width, int(box_height * (2 - symbol_height_scale)))
            else:
                self.text_boxes[name].setGeometry(x, y, box_width, box_height)

    def init_ui(self):
        # just for fun, make the run summary match the game colors
        settings_data = {}
        with open(str(self.file_path).replace("LBAL.save", "LBAL-Settings.save"), 'r') as f:
            settings_data = json.load(f)
        
        background_color = settings_data["colors3"]["background"]
        text_color = settings_data["colors3"]["text_color_misc"]
        selected_font = get_resource_path("fonts/SinsGold.otf")
        if settings_data["display_font"] == 1:
            selected_font = get_resource_path("fonts/NotoSans-Regular.ttf")
        elif settings_data["display_font"] == 2:
            selected_font = get_resource_path("fonts/OpenDyslexic-Regular.ttf")

        self.padding = 2
        self.font_size = 40
        screen_size = QDesktopWidget().screenGeometry()
        screen_width = screen_size.width()
        screen_height = screen_size.height()
        screen_squish = 100

        self.setWindowTitle("Luck Be A Landlord Run Summarizer")
        self.setGeometry(screen_squish, screen_squish, screen_width - (screen_squish * 2), screen_height - (screen_squish * 2))
        self.setStyleSheet(f"background-color: #{background_color};")

        title_height = 100

        # text bounding boxes
        # self.setStyleSheet("QLabel { background-color : lime; }")

        self.text_boxes = {}

        self.text_boxes["title"] = OutlinedLabel(self)
        self.text_boxes["title"].setTextFormat(Qt.RichText)
        self.text_boxes["title"].setOutlineThickness(self.font_size * (1 / 400))
        self.text_boxes["title"].setWordWrap(False)
        self.text_boxes["title"].setText("Luck Be A Landlord Run Summarizer")
        self.text_boxes["title"].setAlignment(Qt.AlignCenter)
        self.text_boxes["title"].setBrush(QColor(f"#{text_color}"))

        font_id = QFontDatabase.addApplicationFont(selected_font)
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        self.custom_font = QFont(font_family, self.font_size)
        self.text_boxes["title"].setFont(self.custom_font)
        self.text_boxes["title"].setGeometry(
            self.padding, self.padding, self.width() - self.padding, title_height - self.padding
        )
        self.text_boxes["title"].setParent(self)

        ui_quad = ["general", "symbols", "items", "bonus"]
        for idx, name in enumerate(ui_quad):
            self.text_boxes[name] = OutlinedLabel(self)
            self.text_boxes[name].setTextFormat(Qt.RichText)
            self.text_boxes[name].setWordWrap(True)
            self.text_boxes[name].setFont(self.custom_font)
            self.text_boxes[name].setAlignment(Qt.AlignCenter)
            self.text_boxes[name].setParent(self)
            self.text_boxes[name].setBrush(QColor(f"#{text_color}"))

        self.update_positions()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_positions()

    def update_text(self, content_dict):
        for name, content in content_dict.items():
            if name in self.text_boxes:
                self.text_boxes[name].setText(content)

    def closeEvent(self, event):
        self.monitor_thread.stop()
        event.accept()

if __name__ == "__main__":
    system = platform.system().lower()
    file_to_monitor = None

    if system == "linux":
        file_to_monitor = Path.home() / ".local" / "share" / "godot" / "app_userdata" / "Luck be a Landlord" / "LBAL.save"
    elif system == "darwin": # macOS
        file_to_monitor = Path.home() / "Library" / "Application" / "Support" / "Godot" / "app_userdata" / "Luck be a Landlord" / "LBAL.save"
    else:
        file_to_monitor = Path.home() / "AppData" / "Roaming" / "Godot" / "app_userdata" / "Luck be a Landlord" / "LBAL.save"

    app = QApplication(sys.argv)
    window = FileMonitorApp(file_to_monitor)
    icon = QIcon(get_resource_path("icon.ico"))
    window.setWindowIcon(icon)
    window.show()
    sys.exit(app.exec_())