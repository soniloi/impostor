GENERATE_TRIGGER = '!'
MYSTERY_TRIGGER = '@'
MYSTERY_NAME = '???'
MYSTERY_START = 'mystery'
MYSTERY_SOLVE = 'solve'

LOOKBACK_LEN = 2 # Number of predecessors to a successor
SOURCEFILE_EXT = ".src" # Source material file extension

BOT_NICK = 'impostor' # Default name of the bot in channel
RANDOM_NICK = 'random' # Word that will trigger a random user to be 'quoted'
ALL_USED = False # Indicates whether there is a nick that will be a composite of all in channel
ALL_NICK = 'all' # Word that denotes nick is composite of all in channel (if used)

INPUT_NICKS_SEP = ':' # Character(s) used to split input nicks
INPUT_NICKS_MAX = 2 # Maximum number of nicks a user can merge

OUTPUT_WORDS_MAX = 200 # The maximum number of words to generate in a line, just to prevent infinite strings
OUTPUT_NICKS_OPEN = '[' # Character(s) before a nick(s)
OUTPUT_NICKS_SEP = ':' # Character(s) between output nicks
OUTPUT_NICKS_CLOSE = '] ' # Character(s) after nick(s)

