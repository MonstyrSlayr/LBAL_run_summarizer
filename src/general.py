import re
import sys
import os

def get_diamond_substrings(text):
    """
    extracts substrings surrounded by diamond brackets
    """
    return re.findall(r'<([^>]*)>', text)

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

def add_line_to_string(string = ""):
    return string + "\n"