# -*- coding: utf-8 -*-

import mock
from mock import patch
import unittest

from bot import players
from bot import processor
from generator import generator
from generator import users

class TestProcessor(unittest.TestCase):

  def setUp(self):

    source_channels = generator.SourceChannelNames("#sea", ["#ocean", "#lake"])
    biggest_users = [
      users.NickAndCount("mollusc", 29),
      users.NickAndCount("lemon", 21),
      users.NickAndCount("quercus", 8),
    ]
    most_quoted_users = [
      users.NickAndCount("lemon", 89),
      users.NickAndCount("amethyst", 41),
    ]

    self.generic_stats = {
      generator.GenericStatisticType.USER_COUNT : 11,
      generator.GenericStatisticType.DATE_STARTED : 1234567890,
      generator.GenericStatisticType.DATE_GENERATED : 1234567,
      generator.GenericStatisticType.SOURCE_CHANNELS : source_channels,
      generator.GenericStatisticType.BIGGEST_USERS : biggest_users,
      generator.GenericStatisticType.MOST_QUOTED_USERS : most_quoted_users
    }

    with patch(generator.__name__ + ".Generator") as generator_mock, \
          patch(players.__name__ + ".PlayerCollection") as players_mock:

      generator_instance = generator_mock.return_value
      generator_instance.empty.return_value = False
      generator_instance.getGenericStatistics.return_value = self.generic_stats

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


  def test_pmd_to_me(self):

    response = self.processor.pmdToMe("mollusc", "whatever")

    self.assertEquals(len(response), 0)


  def test_directed_at_me(self):

    response = self.processor.directedAtMe("mollusc", "whatever")

    self.assertEquals(len(response), 1)
    self.assertEquals(response[0], processor.RequestProcessor.BOT_DESC_BASIC)


  def test_make_stats_no_nick(self):

    expected_stats = "I have material from 11 users. I have been running since 2009-02-13 at 23.31.30. My source " + \
      "material was generated on 1970-01-15 at 07.56.07. Its primary source channel was \x02#sea\x0f, and additional " + \
      "material was drawn from \x02#ocean\x0f and \x02#lake\x0f. The 3 users with the most source material are: " + \
      "\x02mollusc\x0f (29 productions), \x02lemon\x0f (21 productions), and \x02quercus\x0f (8 productions). Since I " + \
      "started keeping records, the user prompted for quotes most often is: \x02lemon\x0f (requested 89 times(s)), " + \
      "followed by \x02amethyst\x0f (41). "

    stats = self.processor.makeStats("mollusc", [])

    self.assertEquals(len(stats), 1)
    self.assertEquals(stats[0], expected_stats)


if __name__ == "__main__":
  unittest.main()

