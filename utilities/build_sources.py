### Read in a series of logs and output personalized source files

import argparse
import os
import string
import sys


OUTPUT_EXTENSION = '.src'

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


def main():

  arg_parser = argparse.ArgumentParser()
  arg_parser.add_argument('--only-existing', dest='only_existing', action='store_true')
  arg_parser.add_argument('--no-only-existing', dest='only_existing', action='store_false')
  arg_parser.add_argument('output_dir')
  arg_parser.add_argument('input_filenames', nargs='+')
  arg_parser.add_argument('-m', dest='merge_filename')
  args = arg_parser.parse_args()

  only_existing=args.only_existing
  input_filenames = args.input_filenames
  merge_filename = args.merge_filename
  output_dirpath = args.output_dir
  if output_dirpath[-1] != os.sep:
    output_dirpath += os.sep

  if not os.path.isdir(output_dirpath):

    if os.path.exists(output_dirpath):
      print "Error: source path exists and is a regular file, exiting"
      sys.exit(1)

    else:
      os.makedirs(output_dirpath)

  # Sometimes, we only want more material from users that already exist
  # In such a case, we only allow nicks we already have source files for
  allowed_nicks = []
  if only_existing == True:
      output_dirpathfiles = os.listdir(output_dirpath)

      for output_dirpathfile in output_dirpathfiles:

          if output_dirpathfile.endswith(OUTPUT_EXTENSION):

              allowed_nick = output_dirpathfile[:-len(OUTPUT_EXTENSION)]
              allowed_nicks.append(allowed_nick)

  if merge_filename:
    mergefile = open(merge_filename)

    for line in mergefile:

      if line:

        nicks = line.split()

        for nick in nicks:
          aliases[nick] = nicks[0]

    mergefile.close()

  for input_filename in input_filenames:
    input_file = open(input_filename)

    for line in input_file:

      opener_index = line.find(NICK_OPEN)
      closer_index = line.find(NICK_CLOSE)

      if line[0].isdigit() and MESSAGE_SIGN not in line and opener_index > -1 and closer_index > opener_index:

        words = line[closer_index+1:].split()

        if len(words) >= 2: # Messages with fewer than two words cannot be used to generate anything useful

          nick = line[opener_index+1:closer_index].translate(None, string.punctuation).split()[0].lower()

          print nick
          if nick in aliases:
            nick = aliases[nick]

          if only_existing == True and nick not in allowed_nicks:
              continue

          output_filepath = output_dirpath + nick + OUTPUT_EXTENSION

          # Write messages to file
          output_file = open(output_filepath, 'a')
          output_line = determine_appropriate_case(words[0])

          for word in words[1:]:
            output_line += ' ' + determine_appropriate_case(word)

          output_file.write(output_line + '\n')
          output_file.close()

    input_file.close()

if __name__ == "__main__":

  main()

