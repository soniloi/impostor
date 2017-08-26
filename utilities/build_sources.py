### Read in a series of logs and output personalized source files

import argparse
import os
import string
import sys

import config


def get_args():

  arg_parser = argparse.ArgumentParser(description='A utility to convert IRC log files into source material for Impostor bot')
  arg_parser.add_argument('output_dir', help='path to directory output is to be written to')
  arg_parser.add_argument('input_filenames', nargs='+', help='paths to input log files')
  arg_parser.add_argument('-m', dest='merge_filename', help='path to the tab-separated file of user aliases')

  only_existing_group = arg_parser.add_mutually_exclusive_group()
  only_existing_group.add_argument('--only-existing', dest='only_existing', action='store_true', help='only generate material for users that already exist')
  only_existing_group.add_argument('--no-only-existing', dest='only_existing', action='store_false', help='do not restrict which users material is generated for')
  arg_parser.set_defaults(only_existing=False)

  return arg_parser.parse_args()


class SourceBuilder:

  def __init__(self, output_dirpath, merge_filename, only_existing):

    self.output_dirpath = output_dirpath
    if output_dirpath[-1] != os.sep:
      self.output_dirpath += os.sep

    SourceBuilder.create_output_directory(output_dirpath)

    self.only_existing = only_existing
    self.allowed_nicks = SourceBuilder.get_allowed_nicks(only_existing, output_dirpath)

    self.aliases = SourceBuilder.init_aliases(merge_filename)


  # Return a case-normalized version of an input token, with exceptions as appropriate
  @staticmethod
  def determine_appropriate_case(word):

    if word in config.CASED_WORDS or word.startswith('http') or word.startswith('www'):
      return word

    else:
      return word.lower()


  @staticmethod
  def create_output_directory(output_dirpath):

    if not os.path.isdir(output_dirpath):

      if os.path.exists(output_dirpath):
        print "Error: source path exists and is a regular file, exiting"
        sys.exit(1)

      else:
        os.makedirs(output_dirpath)


  # Get a list of nicks that we already have source for
  # If only_existing has not been set, return an empty list
  @staticmethod
  def get_allowed_nicks(only_existing, output_dirpath):

    allowed_nicks = []

    if only_existing == True:
      output_dirpathfiles = os.listdir(output_dirpath)

      for output_dirpathfile in output_dirpathfiles:

        if output_dirpathfile.endswith(config.OUTPUT_EXTENSION):

          allowed_nick = output_dirpathfile[:-len(config.OUTPUT_EXTENSION)]
          allowed_nicks.append(allowed_nick)

    return allowed_nicks


  @staticmethod
  def init_aliases(merge_filename):

    aliases = {}

    if merge_filename:
      mergefile = open(merge_filename)

      for line in mergefile:

        if line:

          nicks = line.split()

          for nick in nicks:
            aliases[nick] = nicks[0]

      mergefile.close()

    return aliases


  def process_log_file(self, input_filename):

      input_file = open(input_filename)

      for line in input_file:

        opener_index = line.find(config.NICK_OPEN)
        closer_index = line.find(config.NICK_CLOSE)

        if line[0].isdigit() and config.MESSAGE_SIGN not in line and opener_index > -1 and closer_index > opener_index:

          words = line[closer_index+1:].split()

          if len(words) >= 2: # Messages with fewer than two words cannot be used to generate anything useful

            nick = line[opener_index+1:closer_index].translate(None, string.punctuation).split()[0].lower()

            #print nick
            if nick in self.aliases:
              nick = self.aliases[nick]

            if self.only_existing == True and nick not in self.allowed_nicks:
                continue

            output_filepath = self.output_dirpath + nick + config.OUTPUT_EXTENSION

            # Write messages to file
            output_file = open(output_filepath, 'a')
            output_line = SourceBuilder.determine_appropriate_case(words[0])

            for word in words[1:]:
              output_line += ' ' + SourceBuilder.determine_appropriate_case(word)

            output_file.write(output_line + '\n')
            output_file.close()

      input_file.close()


  def generate(self, input_filenames):

    for input_filename in input_filenames:
      self.process_log_file(input_filename)


def main():

  args = get_args()

  generator = SourceBuilder(args.output_dir, args.merge_filename, args.only_existing)
  generator.generate(args.input_filenames)


if __name__ == "__main__":

  main()

