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

    self.mollusc_stats = {
      users.UserStatisticType.REAL_NICK : "mollusc",
      users.UserStatisticType.ALIASES : (["mollusc_", "snail", "limpet"], "limpet"),
      users.UserStatisticType.PRODUCTION_COUNT : 12345,
      users.UserStatisticType.QUOTES_REQUESTED : 91,
    }

    with patch(generator.__name__ + ".Generator") as generator_mock, \
          patch(players.__name__ + ".PlayerCollection") as players_mock:

      self.generator_instance = generator_mock.return_value
      self.generator_instance.empty.return_value = False
      self.generator_instance.getGenericStatistics.return_value = self.generic_stats

      self.players_instance = players_mock.return_value

      self.processor = processor.RequestProcessor("", self.generator_instance, self.players_instance)


  def user_statistics_side_effect(self, *args):

    if args[0] == "mollusc":
      return self.mollusc_stats

    return None


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

    stats = self.processor.makeStats("mollusc", ["stats"])

    self.assertEquals(len(stats), 1)
    self.assertEquals(stats[0], expected_stats)


  def test_make_stats_one_nick_unknown(self):

    stats = self.processor.makeStats("mollusc", ["stats", "unknown"])

    self.assertEquals(len(stats), 1)
    self.assertEquals(len(stats[0]), 0)


  def test_make_stats_one_nick_known(self):

    expected_start = "The user \x02mollusc\x0f (AKA "
    expected_end = ") has 12345 production(s). 91 quote(s) have been requested of them. "

    self.generator_instance.getUserStatistics.side_effect = self.user_statistics_side_effect

    stats = self.processor.makeStats("mollusc", ["stats", "mollusc"])

    self.assertEquals(len(stats), 1)
    self.assertTrue(stats[0].startswith(expected_start))
    self.assertTrue(stats[0].endswith(expected_end))
    self.assertTrue("mollusc_" in stats[0])
    self.assertTrue("snail" in stats[0])
    self.assertTrue("limpet" in stats[0])


  def test_make_stats_two_nick(self):

    expected_start = "The user \x02mollusc\x0f (AKA "
    expected_end = ") has 12345 production(s). 91 quote(s) have been requested of them. "

    self.generator_instance.getUserStatistics.side_effect = self.user_statistics_side_effect

    stats = self.processor.makeStats("mollusc", ["stats", "mollusc", "someoneelse"])

    self.assertEquals(len(stats), 1)
    self.assertTrue(stats[0].startswith(expected_start))
    self.assertTrue(stats[0].endswith(expected_end))


  def test_start_mystery_new(self):

    mystery_nick = "quercus"
    mystery_quote = "hello there"
    generate_result = ([mystery_nick], mystery_quote)
    self.generator_instance.generate.return_value = generate_result

    response = self.processor.startMystery("", [])

    self.assertEquals(response[0], "The mystery author says: [%s]. " % mystery_quote)
    self.assertIsNotNone(self.processor.current_mystery)
    self.assertEquals(self.processor.current_mystery.author, mystery_nick)


  def test_start_mystery_existing(self):

    mystery_nick = "quercus"
    mystery_quote = "hello there"
    generate_result = ([mystery_nick], mystery_quote)
    self.generator_instance.generate.return_value = generate_result

    response = self.processor.startMystery("", [])
    first_response = response[0]
    first_mystery_ident = self.processor.next_mystery_ident

    response = self.processor.startMystery("", [])

    # Ensure mystery quote and ident number are unchanged
    self.assertEquals(response[0], first_response)
    self.assertEquals(self.processor.next_mystery_ident, first_mystery_ident)


  def test_guess_mystery_none(self):

    response = self.processor.guessMystery("mollusc", [])

    self.assertEquals(len(response), 1)
    self.assertEquals(response[0], processor.RequestProcessor.NO_MYSTERY)


  def test_guess_mystery_existing_incorrect(self):

    mystery_nick = "quercus"
    mystery_quote = "hello there"
    generate_result = ([mystery_nick], mystery_quote)
    self.generator_instance.generate.return_value = generate_result
    self.processor.startMystery("", [])

    response = self.processor.guessMystery("mollusc", ["guess", "lemon"])

    self.assertEquals(len(response), 1)
    self.assertEquals(len(response[0]), 0)
    self.assertIsNotNone(self.processor.current_mystery)


  def test_guess_mystery_existing_incorrect(self):

    mystery_nick = "quercus"
    mystery_quote = "hello there"
    generate_result = ([mystery_nick], mystery_quote)
    self.generator_instance.generate.return_value = generate_result
    self.processor.startMystery("", [])

    response = self.processor.guessMystery("mollusc", ["guess", "quercus"])

    self.assertEquals(len(response), 1)
    self.assertEquals(response[0], "The mystery author was: quercus. Congratulations, mollusc! ")
    self.assertIsNone(self.processor.current_mystery)


if __name__ == "__main__":
  unittest.main()

