### Read in a series of logs and output personalized source files

import argparse
import os
import string
import sys

import config

aliases = {}

# Return a case-normalized version of an input token, with exceptions as appropriate
def determine_appropriate_case(word):

  if word in config.CASED_WORDS or word.startswith('http') or word.startswith('www'):
    return word

  else:
    return word.lower()


def get_args():

  arg_parser = argparse.ArgumentParser(description='A utility to convert IRC log files into source material for Impostor bot')
  arg_parser.add_argument('--only-existing', dest='only_existing', action='store_true', help='only generate material for users that already exist')
  arg_parser.add_argument('--no-only-existing', dest='only_existing', action='store_false', help='do not restrict which users material is generated for')
  arg_parser.add_argument('output_dir', help='path to directory output is to be written to')
  arg_parser.add_argument('input_filenames', nargs='+', help='paths to input log files')
  arg_parser.add_argument('-m', dest='merge_filename', help='path to the tab-separated file of user aliases')
  return arg_parser.parse_args()


def main():

  args = get_args()

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

          if output_dirpathfile.endswith(config.OUTPUT_EXTENSION):

              allowed_nick = output_dirpathfile[:-len(config.OUTPUT_EXTENSION)]
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

      opener_index = line.find(config.NICK_OPEN)
      closer_index = line.find(config.NICK_CLOSE)

      if line[0].isdigit() and config.MESSAGE_SIGN not in line and opener_index > -1 and closer_index > opener_index:

        words = line[closer_index+1:].split()

        if len(words) >= 2: # Messages with fewer than two words cannot be used to generate anything useful

          nick = line[opener_index+1:closer_index].translate(None, string.punctuation).split()[0].lower()

          print nick
          if nick in aliases:
            nick = aliases[nick]

          if only_existing == True and nick not in allowed_nicks:
              continue

          output_filepath = output_dirpath + nick + config.OUTPUT_EXTENSION

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

