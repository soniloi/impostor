# -*- coding: utf-8 -*-

import unittest

from utilities.build_sources import SourceBuilder


class TestSourceBuilder(unittest.TestCase):

  def setUp(self):

    self.output_dir_base = "output/"
    self.builder = SourceBuilder(self.output_dir_base, False)


  def test_init_empty(self):

    builder = SourceBuilder("output/", False)

    self.assertFalse(builder.only_existing)
    self.assertEquals(len(builder.existing_nicks), 0)
    self.assertEquals(len(builder.aliases), 0)


  def test_init_configured(self):

    existing_filenames = ["mollusc.src", "lemon.src", "quercus.src", "nobody.txt"]
    merge_content = [
      "mollusc\tmollusc_\tsnail",
      "quercus\toak",
    ]

    self.builder.configure_nicks(existing_filenames, merge_content)

    self.assertFalse(self.builder.only_existing)
    self.assertEquals(len(self.builder.existing_nicks), 3)
    self.assertEquals(len(self.builder.aliases), 5)
    self.assertEquals(self.builder.aliases["mollusc"], "mollusc")
    self.assertEquals(self.builder.aliases["mollusc_"], "mollusc")
    self.assertEquals(self.builder.aliases["snail"], "mollusc")
    self.assertEquals(self.builder.aliases["quercus"], "quercus")
    self.assertEquals(self.builder.aliases["oak"], "quercus")


  def test_process_line_empty(self):

    line = "12.34.56 [mollusc]"
    output = self.builder.process_line(line)

    self.assertFalse(output)


  def test_process_line_only_whitespace(self):

    line = "12.34.56 [mollusc]        "
    output = self.builder.process_line(line)

    self.assertFalse(output)


  def test_process_line_short(self):

    line = "12.34.56 [mollusc] hello"
    output = self.builder.process_line(line)

    self.assertFalse(output)


  def test_process_line_no_timestamp(self):

    line = "[mollusc] hello there"
    output = self.builder.process_line(line)

    self.assertFalse(output)


  def test_process_line_lookback_length(self):

    line = "12.34.56 [mollusc] hello there"
    (output_filepath, output_line) = self.builder.process_line(line)

    self.assertEquals(output_filepath, self.output_dir_base + "mollusc.src")
    self.assertEquals(output_line, "hello there")


  def test_process_line_long(self):

    line = "12.34.56 [mollusc] hello there, from inside my shell"
    (output_filepath, output_line) = self.builder.process_line(line)

    self.assertEquals(output_line, "hello there, from inside my shell")


  def test_process_line_normalizing_whitespace(self):

    line = "12.34.56 [mollusc]  hello\t  there      "
    (output_filepath, output_line) = self.builder.process_line(line)

    self.assertEquals(output_line, "hello there")


  def test_process_line_normalizing_case(self):

    line = "12.34.56 [mollusc] Hello ThErE"
    (output_filepath, output_line) = self.builder.process_line(line)

    self.assertEquals(output_line, "hello there")


  def test_process_line_normalizing_smiley(self):

    line = "12.34.56 [mollusc] hello there :D"
    (output_filepath, output_line) = self.builder.process_line(line)

    self.assertEquals(output_line, "hello there :D")


if __name__ == "__main__":
  unittest.main()

