GENERATE_TRIGGER = '!'
META_TRIGGER = '@'

META_HELP = ['?', 'help', 'impostor']

META_STATS = 'stats'

MYSTERY_START = 'mystery'
MYSTERY_GUESS = 'guess'
MYSTERY_HINT = 'hint'
MYSTERY_SOLVE = 'solve'
MYSTERY_MIN_STARTERS = 1000 # Minimum number of starter tuples a user must have before the mystery generator will generate a quote from them
MYSTERY_HINTS_MAX = 3

LOOKBACK_LEN = 2 # Number of predecessors to a successor
SOURCEFILE_EXT = ".src" # Source material file extension

META_FILE_NAME = "meta.info" # Meta info file inside sources directory
META_DATE = "date"
META_PRIMARY = "primary"
META_ADDITIONAL = "additional"

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

