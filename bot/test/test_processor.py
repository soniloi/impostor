# -*- coding: utf-8 -*-

import mock
from mock import patch
import unittest

from bot import players
from bot import processor
from generator import generator

class TestProcessor(unittest.TestCase):

  def setUp(self):

    with patch(generator.__name__ + ".Generator") as generator_mock, \
          patch(players.__name__ + ".PlayerCollection") as players_mock:

      generator_instance = generator_mock.return_value
      generator_instance.empty.return_value = False

      players_instance = players_mock.return_value

      self.processor = processor.RequestProcessor("", generator_instance, players_instance)


  def test_init(self):

    self.assertTrue("stats" in self.processor.commands)
    self.assertTrue("?" in self.processor.commands)


  def test_trigger_meta_help_generic(self):

    response = self.processor.triggerMeta("mollusc", "@help")

    self.assertEquals(len(response), 1)
    self.assertEquals(response[0], processor.RequestProcessor.BOT_DESC_BASIC)


  def test_trigger_meta_help_specific_unknown(self):

    response = self.processor.triggerMeta("mollusc", "@help nonsense")

    self.assertEquals(len(response), 0)


  def test_trigger_meta_help_specific_known(self):

    response = self.processor.triggerMeta("mollusc", "@help mystery")

    self.assertEquals(len(response), 1)
    self.assertEquals(response[0], processor.RequestProcessor.HELP_MYSTERY)


if __name__ == "__main__":
  unittest.main()

