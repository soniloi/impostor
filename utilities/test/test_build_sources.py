# -*- coding: utf-8 -*-

import unittest

from utilities.build_sources import SourceBuilder


class TestSourceBuilder(unittest.TestCase):

  def setUp(self):

    pass


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

    builder = SourceBuilder("output/", False)
    builder.configure_nicks(existing_filenames, merge_content)

    self.assertFalse(builder.only_existing)
    self.assertEquals(len(builder.existing_nicks), 3)
    self.assertEquals(len(builder.aliases), 5)
    self.assertEquals(builder.aliases["mollusc"], "mollusc")
    self.assertEquals(builder.aliases["mollusc_"], "mollusc")
    self.assertEquals(builder.aliases["snail"], "mollusc")
    self.assertEquals(builder.aliases["quercus"], "quercus")
    self.assertEquals(builder.aliases["oak"], "quercus")


if __name__ == "__main__":
  unittest.main()

