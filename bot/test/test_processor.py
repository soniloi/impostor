# -*- coding: utf-8 -*-

import mock
from mock import patch
import unittest

from bot import players
from bot import processor
from generator import generator

class TestProcessor(unittest.TestCase):

  def setUp(self):

    pass


  def test_init(self):

    with patch(generator.__name__ + ".Generator") as generator_mock, \
          patch(players.__name__ + ".PlayerCollection") as players_mock:

      generator_instance = generator_mock.return_value
      generator_instance.empty.return_value = False

      players_instance = players_mock.return_value

      proc = processor.RequestProcessor("", generator_instance, players_instance)

      self.assertTrue("stats" in proc.commands)
      self.assertTrue("?" in proc.commands)


if __name__ == "__main__":
  unittest.main()

