GENERATE_TRIGGER = '!'
META_TRIGGER = '@'

META_HELP = ['?', 'help', 'impostor']

META_STATS = 'stats'

MYSTERY_START = 'mystery'
MYSTERY_GUESS = 'guess'
MYSTERY_HINT = 'hint'
MYSTERY_SOLVE = 'solve'
MYSTERY_MIN_STARTERS = 1000 # Minimum number of starter tuples a user must have before the mystery generator will generate a quote from them
MYSTERY_CHARACTER_HINTS_MAX = 3 # Maximum number of nick-character hints that will be given under any circumstances
MYSTERY_WORDS_MAX_FOR_SECOND = 5 # A second quote hint will only be given if the first consisted of this number of words or fewer

MERGEINFO_ALIASES_MAX = 3 # Display at most this number of aliases when listing

BOT_NICK = 'impostor' # Default name of the bot in channel
RANDOM_NICK = 'random' # Word that will trigger a random user to be 'quoted'
ALL_USED = False # Indicates whether there is a nick that will be a composite of all in channel
ALL_NICK = 'all' # Word that denotes nick is composite of all in channel (if used)

INPUT_NICKS_SEP = ':' # Character(s) used to split input nicks
INPUT_NICKS_MAX = 2 # Maximum number of nicks a user can merge

OUTPUT_NICKS_OPEN = '[' # Character(s) before a nick(s)
OUTPUT_NICKS_SEP = ':' # Character(s) between output nicks
OUTPUT_NICKS_CLOSE = '] ' # Character(s) after nick(s)

REPOSITORY = 'https://github.com/soniloi/impostor'

