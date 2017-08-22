### Read in a series of logs and output personalized source files

import argparse
import os
import string
import sys


srcdir = './sources/' # Where the personalized sources are to be written to
srcext = '.src'
mergefilename = './merge.lst'

NICK_OPEN = '['
NICK_CLOSE = ']'
MESSAGE_SIGN = '-!-'

aliases = {}

retain = ["I", "I'd", "I'm", "I've", ":D", ":O", ":P", ":S", ">:D", "D:", "T_T"] # Words not to be lower-cased

# Return a case-normalized version of an input token, with exceptions as appropriate
def determine_appropriate_case(word):
  if word in retain or word.startswith('http') or word.startswith('www'):
    return word
  else:
    return word.lower()

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('--only-existing', dest='only_existing', action='store_true')
arg_parser.add_argument('--no-only-existing', dest='only_existing', action='store_false')
arg_parser.add_argument('-f', dest='infilenames', nargs='+')
args = arg_parser.parse_args()

only_existing=args.only_existing
infilenames = args.infilenames

if not os.path.isdir(srcdir):
  if os.path.exists(srcdir):
    print "Error: source path exists and is a regular file, exiting"
    sys.exit(1)
  else:
    os.makedirs(srcdir)

# Sometimes, we only want more material from users that already exist
# In such a case, we only allow nicks we already have source files for
allowed_nicks = []
if only_existing == True:
    srcdirfiles = os.listdir(srcdir)
    for srcdirfile in srcdirfiles:
        if srcdirfile.endswith(srcext):
            allowed_nick = srcdirfile[:-len(srcext)]
            allowed_nicks.append(allowed_nick)

mergefile = open(mergefilename)
for line in mergefile:
  if line:
    nicks = line.split()
    for nick in nicks:
      aliases[nick] = nicks[0]
mergefile.close()

for infilename in infilenames:
  infile = open(infilename)

  for line in infile:

    opener_index = line.find(NICK_OPEN)
    closer_index = line.find(NICK_CLOSE)

    if line[0].isdigit() and MESSAGE_SIGN not in line and opener_index > -1 and closer_index > opener_index:

      words = line[closer_index:].split()

      if len(words) >= 2: # Messages with fewer than two words cannot be used to generate anything useful

        nick = line[opener_index+1:closer_index].translate(None, string.punctuation).split()[0].lower()

        print nick
        if nick in aliases:
          nick = aliases[nick]

        if only_existing == True and nick not in allowed_nicks:
            continue

        outfilename = srcdir + nick + srcext

        # Write messages to file
        outfile = open(outfilename, 'a')
        outline = determine_appropriate_case(words[0])

        for word in words[1:]:
          outline += ' ' + determine_appropriate_case(word)

        outfile.write(outline + '\n')
        outfile.close()

  infile.close()