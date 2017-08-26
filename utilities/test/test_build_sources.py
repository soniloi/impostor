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


if __name__ == "__main__":
  unittest.main()

