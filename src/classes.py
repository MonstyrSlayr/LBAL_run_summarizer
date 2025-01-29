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