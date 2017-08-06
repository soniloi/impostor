LOOKBACK_LEN = 2 # Number of predecessors to a successor
SOURCEFILE_EXT = ".src" # Source material file extension

META_FILE_NAME = "meta.info" # Meta info file inside sources directory
META_DATE = "date"
META_PRIMARY = "primary"
META_ADDITIONAL = "additional"

BIGGEST_USERS_COUNT = 3 # Number of biggest users to display
MOST_QUOTED_COUNT = 3 # Number of most quoted users to display
MERGEINFO_FILE_NAME = "merge.lst" # User merge list file inside sources directory
STATS_FILE_NAME = "users.p" # File to save user stats to
CHANGES_BETWEEN_STATS_PERSISTENCE = 5 # Number of changes seen between stats writes to disk

OUTPUT_WORDS_MAX = 200 # The maximum number of words to generate in a line, just to prevent infinite strings

# Pairs of parentheses and other punctuation to search for in matching
OPENERS_TO_CLOSERS = {
  "(" : ")",
  "[" : "]",
  "{" : "}",
  "\"" : "\"",
}
CLOSERS_TO_OPENERS = {
  v: k for k, v in OPENERS_TO_CLOSERS.iteritems()
}

# Set of tokens that should be ignored in parenthesis matching
PARENTHESIS_EXCEPTIONS = {
  "(:",
  "(:<)"
  "):",
  "):<",
  ":(",
  ">:(",
  ":)",
  ">:)",
}

WORD_ENDING_PUNCTUATION = [
  ".",
  "?",
  "!",
  ",",
  ":",
  ";",
]

