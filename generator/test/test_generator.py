# -*- coding: utf-8 -*-

import mock
from mock import patch
import unittest

from generator import config
from generator import users
from generator.generator import Generator
from generator.generator import GeneratorUtil
from generator.generator import GenericStatisticType
from generator.users import UserNickType


class TestGenerator(unittest.TestCase):

  def setUp(self):

    self.rain_nick = "rain"
    self.aliases = {
      self.rain_nick : ["rain_", "fearthainn"],
    }
    self.stats = {
      self.rain_nick : "statistics",
    }

    self.saoi_nick = "saoi"
    self.file_nick = "file"
    self.bard_nick = "bard"

    self.quotes = {
      self.saoi_nick : "is glas iad na cnoic i bhfad uainn",
      self.file_nick : "marbh le tae agus marbh gan é",
      self.bard_nick : "(: is olc (an ghaoth (nach séideann maith), do dhuine éigin >:)) {mar a :) deirtear}",
    }

    self.starters = {}
    self.starters[self.saoi_nick] = [("is", "glas")]
    self.starters[self.file_nick] = [("marbh", "le")]
    self.starters[self.bard_nick] = [("(:", "is")]

    self.generic_lookbacks = {}
    self.generic_lookbacks[self.saoi_nick] = {
      ("is", "glas") : ["iad"],
      ("glas", "iad") : ["na"],
      ("iad", "na") : ["cnoic"],
      ("na", "cnoic") : ["i"],
      ("cnoic", "i") : ["bhfad"],
      ("i", "bhfad") : ["uainn"],
      ("bhfad", "uainn") : [GeneratorUtil.TERMINATE],
    }
    self.generic_lookbacks[self.file_nick] = {
      ("marbh", "le") : ["tae"],
      ("le", "tae") : ["agus"],
      ("tae", "agus") : ["marbh"],
      ("agus", "marbh") : ["gan"],
      ("marbh", "gan") : ["é"],
      ("gan", "é") : [GeneratorUtil.TERMINATE],
    }
    self.generic_lookbacks[self.bard_nick] = {
      ("(:", "is") : ["olc"],
      ("is", "olc") : ["(an"],
      ("olc", "(an") : ["ghaoth]"],
      ("(an", "ghaoth]") : ["(nach"],
      ("ghaoth]", "(nach") : ["séideann"],
      ("(nach", "séideann") : ["eile"],
      ("séideann", "maith),") : ["do"],
      ("maith),", "do") : ["dhuine"],
      ("do", "dhuine") : ["éigin"],
      ("dhuine", "éigin") : ["eile"],
      ("éigin", ">:))") : ["{mar"],
      (">:))", "{mar") : ["a"],
      ("{mar", "a") : [":)"],
      ("a", ":)") : ["deirtear"],
      ("a", "deirtear") : [GeneratorUtil.TERMINATE],
    }

    self.closing_lookbacks = {}
    self.closing_lookbacks[self.saoi_nick] = {"(":{}, "{":{}, "[":{}, "\"":{}}
    self.closing_lookbacks[self.file_nick] = {"(":{}, "{":{}, "[":{}, "\"":{}}
    self.closing_lookbacks[self.bard_nick] = {
      "(" : {
        ("(nach", "séideann") : ["maith),"],
        ("dhuine", "éigin") : [">:))"],
      },
      "{":{}, "[":{}, "\"":{},
    }

    self.generator = Generator()

    with patch(users.__name__ + ".UserCollection") as users_mock:

      self.users_instance = users_mock.return_value


  @staticmethod
  def retrieve_value_or_default(dictionary, key, default):

    if key in dictionary:
      return dictionary[key]

    return default


  def aliases_side_effect(self, *args):

    return TestGenerator.retrieve_value_or_default(self.aliases, args[0], [])


  def stats_side_effect(self, *args):

    return TestGenerator.retrieve_value_or_default(self.stats, args[0], None)


  def starters_side_effect(self, *args):

    return TestGenerator.retrieve_value_or_default(self.starters, args[0], [])


  def generic_lookbacks_side_effect(self, *args):

    return TestGenerator.retrieve_value_or_default(self.generic_lookbacks, args[0], {})


  def closing_lookbacks_side_effect(self, *args):

    return TestGenerator.retrieve_value_or_default(self.closing_lookbacks, args[0], {})


  def test_copy_list_dict(self):

    rain_key = "rain"

    focloir = {
      rain_key : ["fearthainn", "báisteach"],
    }

    copy = GeneratorUtil.copyListDict(focloir)

    self.assertTrue(copy)
    self.assertEqual(copy, focloir)

    # Check that the list is new
    self.assertFalse(copy[rain_key] is focloir[rain_key])

    # Check that the list elements are not new
    for i in range(0, len(copy[rain_key])):
      self.assertTrue(copy[rain_key][i] is focloir[rain_key][i])


  def test_merge_into_dictionary_no_matching_keys(self):

    tree_key = "tree"
    tree_value = ["crann"]

    rain_key = "rain"
    rain_value = ["báisteach"]

    focloir1 = {
      tree_key : tree_value,
    }

    focloir2 = {
      rain_key : rain_value,
    }

    GeneratorUtil.mergeIntoDictionary(focloir1, focloir2)

    # Ensure first dictionary has been mutated correctly
    self.assertEqual(len(focloir1), 2)
    self.assertTrue(tree_key in focloir1)
    self.assertTrue(rain_key in focloir1)
    self.assertEqual(focloir1[tree_key], tree_value)
    self.assertEqual(focloir1[rain_key], rain_value)

    self.assertTrue(focloir1[tree_key] is tree_value)
    self.assertTrue(focloir1[rain_key] is not rain_value)
    self.assertTrue(focloir1[rain_key][0] is rain_value[0])

    # Ensure second dictionary is unchanged
    self.assertEqual(len(focloir2), 1)
    self.assertTrue(rain_key in focloir2)

    self.assertEqual(len(focloir2[rain_key]), 1)
    self.assertTrue(focloir2[rain_key] is rain_value)
    self.assertTrue(focloir2[rain_key][0] is rain_value[0])


  def test_merge_into_dictionary_with_matching_keys(self):

    rain_key = "rain"
    rain_elem1 = "fearthainn"
    rain_elem2 = "báisteach"
    rain_value1 = [rain_elem1]
    rain_value2 = [rain_elem2]

    focloir1 = {
      rain_key : rain_value1,
    }

    focloir2 = {
      rain_key : rain_value2,
    }

    GeneratorUtil.mergeIntoDictionary(focloir1, focloir2)

    # Ensure first dictionary has been mutated correctly
    self.assertEqual(len(focloir1), 1)
    self.assertTrue(rain_key in focloir1)
    self.assertEqual(focloir1[rain_key], [rain_elem1, rain_elem2])

    self.assertTrue(focloir1[rain_key] is rain_value1)
    self.assertTrue(focloir1[rain_key][0] is rain_value1[0])
    self.assertTrue(focloir1[rain_key][1] is rain_value2[0])

    # Ensure second dictionary is unchanged
    self.assertEqual(len(focloir2), 1)
    self.assertTrue(rain_key in focloir2)

    self.assertEqual(len(focloir2[rain_key]), 1)
    self.assertTrue(rain_key in focloir2)
    self.assertTrue(focloir2[rain_key] is rain_value2)
    self.assertTrue(focloir2[rain_key][0] is rain_value2[0])


  def test_init_empty(self):

    self.users_instance.empty.return_value = True

    self.generator.init(self.users_instance, {}, 0)
    self.assertTrue(self.generator.empty())


  def test_process_source_generic(self):

    source_nick = "almond"
    source_filename = source_nick + ".src"
    source_data = [
      "a b c d",
      "a b c e",
      "f g h",
      "i j",
      "k",
    ]

    (nick, starters, generic_lookbacks, closing_lookbacks) = self.generator.processSource(source_filename, source_data)

    ab = ("a", "b")
    bc = ("b", "c")
    cd = ("c", "d")
    ce = ("c", "e")
    fg = ("f", "g")
    gh = ("g", "h")
    ij = ("i", "j")

    self.assertEqual(nick, source_nick)

    self.assertEqual(len(starters), 4)
    self.assertTrue(ab in starters)
    self.assertTrue(fg in starters)

    self.assertEqual(len(generic_lookbacks), 7)
    self.assertTrue(ab in generic_lookbacks)
    self.assertTrue(bc in generic_lookbacks)
    self.assertTrue(cd in generic_lookbacks)
    self.assertTrue(ce in generic_lookbacks)
    self.assertTrue(fg in generic_lookbacks)
    self.assertTrue(gh in generic_lookbacks)
    self.assertTrue(ij in generic_lookbacks)

    self.assertEqual(len(generic_lookbacks[ab]), 2)
    self.assertTrue("c" in generic_lookbacks[ab])
    self.assertEqual(generic_lookbacks[ab][0], generic_lookbacks[ab][1])

    self.assertEqual(len(generic_lookbacks[bc]), 2)
    self.assertTrue("d" in generic_lookbacks[bc])
    self.assertTrue("e" in generic_lookbacks[bc])

    self.assertEqual(len(generic_lookbacks[cd]), 1)
    self.assertTrue(GeneratorUtil.TERMINATE in generic_lookbacks[cd])

    self.assertEqual(len(generic_lookbacks[ce]), 1)
    self.assertTrue(GeneratorUtil.TERMINATE in generic_lookbacks[ce])

    self.assertEqual(len(generic_lookbacks[fg]), 1)
    self.assertTrue("h" in generic_lookbacks[fg])

    self.assertEqual(len(generic_lookbacks[gh]), 1)
    self.assertTrue(GeneratorUtil.TERMINATE in generic_lookbacks[gh])

    self.assertEqual(len(generic_lookbacks[ij]), 1)
    self.assertTrue(GeneratorUtil.TERMINATE in generic_lookbacks[ij])

    self.assertEqual(len(closing_lookbacks), 4)
    self.assertFalse(closing_lookbacks["("])
    self.assertFalse(closing_lookbacks["["])
    self.assertFalse(closing_lookbacks["\""])
    self.assertFalse(closing_lookbacks["{"])


  def test_process_source_closer_nonsmileys(self):

    source_data = ["a) b c d", "a b} c d", "a b c] d)", "a] b} c) d\""]

    (nick, starters, generic_lookbacks, closing_lookbacks) = self.generator.processSource("almond.src", source_data)

    self.assertEqual(len(generic_lookbacks), 11)
    self.assertEqual(len(generic_lookbacks[("c", "d")]), 2)
    self.assertEqual(len(closing_lookbacks), 4)
    self.assertEqual(len(closing_lookbacks["("]), 2)
    self.assertEqual(len(closing_lookbacks["["]), 1)
    self.assertEqual(len(closing_lookbacks["\""]), 1)
    self.assertEqual(closing_lookbacks["("], {('a]', 'b}'): ['c)'], ('b', 'c]'): ['d)']})
    self.assertEqual(closing_lookbacks["["], {('a', 'b'): ['c]']})
    self.assertEqual(closing_lookbacks["\""], {('b}', 'c)'): ['d"']})
    self.assertFalse(closing_lookbacks["{"])


  def test_process_source_closer_smileys(self):

    source_data = [":) b c d", "a :) c d", "a b :) d", "a b c :)"]

    (nick, starters, generic_lookbacks, closing_lookbacks) = self.generator.processSource("almond.src", source_data)

    self.assertEqual(len(generic_lookbacks), 9)
    self.assertEqual(len(generic_lookbacks[("a", "b")]), 2)
    self.assertEqual(len(generic_lookbacks[("b", "c")]), 2)
    self.assertEqual(len(generic_lookbacks[("c", "d")]), 2)
    self.assertEqual(len(closing_lookbacks), 4)
    self.assertFalse(closing_lookbacks["("])
    self.assertFalse(closing_lookbacks["["])
    self.assertFalse(closing_lookbacks["\""])
    self.assertFalse(closing_lookbacks["{"])


  def test_process_source_closer_urls_opened(self):

    source_data = [
      "http://a.b.com(s) b c d",
      "a http://a.b.com(s) c d",
      "a b http://a.b.com(s) d",
      "a b c http://a.b.com(s)",
      "d e f http://a.b.com(s))z",
    ]

    (nick, starters, generic_lookbacks, closing_lookbacks) = self.generator.processSource("almond.src", source_data)

    self.assertEqual(len(closing_lookbacks), 4)
    self.assertFalse(closing_lookbacks["("])
    self.assertFalse(closing_lookbacks["["])
    self.assertFalse(closing_lookbacks["\""])
    self.assertFalse(closing_lookbacks["{"])


  def test_process_source_closer_urls_unopened(self):

    source_data = [
      "http://a.b.com) b c d",
      "a http://a.b.com) c d",
      "a b http://a.b.com) d",
      "a b c http://a.b.com)",
      "d e f http://a.b.com(s))",
    ]

    (nick, starters, generic_lookbacks, closing_lookbacks) = self.generator.processSource("almond.src", source_data)

    self.assertEqual(len(closing_lookbacks), 4)
    self.assertEqual(len(closing_lookbacks["("]), 3)
    self.assertTrue(("a", "b") in closing_lookbacks["("])
    self.assertTrue(("b", "c") in closing_lookbacks["("])
    self.assertFalse(closing_lookbacks["["])
    self.assertFalse(closing_lookbacks["\""])
    self.assertFalse(closing_lookbacks["{"])


  def test_get_generic_statistics_empty(self):

    time = 818
    user_count = 0

    self.users_instance.countUsers.return_value = user_count
    self.users_instance.getBiggestUsers.return_value = None
    self.users_instance.getMostQuoted.return_value = None

    self.generator.init(self.users_instance, {}, time)
    stats = self.generator.getGenericStatistics()

    self.assertTrue(GenericStatisticType.USER_COUNT in stats)
    self.assertTrue(GenericStatisticType.DATE_STARTED in stats)
    self.assertTrue(GenericStatisticType.DATE_GENERATED in stats)
    self.assertTrue(GenericStatisticType.SOURCE_CHANNELS in stats)
    self.assertTrue(GenericStatisticType.BIGGEST_USERS in stats)
    self.assertTrue(GenericStatisticType.MOST_QUOTED_USERS in stats)

    self.assertEqual(stats[GenericStatisticType.USER_COUNT], user_count)
    self.assertEqual(stats[GenericStatisticType.DATE_STARTED], time)
    self.assertEqual(stats[GenericStatisticType.DATE_GENERATED], None)

    source_channels = stats[GenericStatisticType.SOURCE_CHANNELS]
    self.assertEqual(source_channels.primary, None)
    self.assertFalse(source_channels.additionals)

    self.assertEqual(stats[GenericStatisticType.BIGGEST_USERS], None)
    self.assertEqual(stats[GenericStatisticType.MOST_QUOTED_USERS], None)


  def test_get_generic_statistics_nonempty(self):

    primary = "#ocean"
    additional = ["#pond", "#sea", "#lake"]

    meta = {
      config.META_PRIMARY: [primary],
      config.META_ADDITIONAL: additional,
    }

    time = 97
    user_count = 3

    user_nick_1 = "ailm"
    user_nick_2 = "beith"
    user_nick_3 = "coll"

    big_users = [
      users.NickAndCount(user_nick_1, 79),
      users.NickAndCount(user_nick_1, 23),
      users.NickAndCount(user_nick_1, 11),
    ]

    quoted_users = [
      users.NickAndCount(user_nick_3, 346),
      users.NickAndCount(user_nick_1, 129),
      users.NickAndCount(user_nick_2, 62),
    ]

    self.users_instance.countUsers.return_value = user_count
    self.users_instance.getBiggestUsers.return_value = big_users
    self.users_instance.getMostQuoted.return_value = quoted_users

    self.generator.init(self.users_instance, meta, time)
    stats = self.generator.getGenericStatistics()

    self.assertEqual(stats[GenericStatisticType.USER_COUNT], user_count)
    self.assertEqual(stats[GenericStatisticType.DATE_STARTED], time)
    self.assertEqual(stats[GenericStatisticType.DATE_GENERATED], None)

    source_channels = stats[GenericStatisticType.SOURCE_CHANNELS]
    self.assertEqual(source_channels.primary, primary)
    self.assertEqual(source_channels.additionals, tuple(additional))

    self.assertEqual(stats[GenericStatisticType.BIGGEST_USERS], big_users)
    self.assertEqual(stats[GenericStatisticType.MOST_QUOTED_USERS], quoted_users)


  def test_get_user_aliases(self):

    self.users_instance.getUserAliases.side_effect = self.aliases_side_effect

    self.generator.init(self.users_instance, {}, 0)
    aliases = self.generator.getUserAliases(self.rain_nick)

    self.assertEqual(aliases, self.aliases[self.rain_nick])
    self.assertTrue(aliases is self.aliases[self.rain_nick])


  def test_get_user_statistics_unknown(self):

    self.users_instance.getUserStatistics.side_effect = self.stats_side_effect

    self.generator.init(self.users_instance, {}, 0)
    stats = self.generator.getUserStatistics("unknown")
    self.assertEqual(stats, None)


  def test_get_user_statistics_known(self):

    self.users_instance.getUserStatistics.side_effect = self.stats_side_effect

    self.generator.init(self.users_instance, {}, 0)
    stats = self.generator.getUserStatistics(self.rain_nick)

    self.assertTrue(stats)
    self.assertEqual(stats, self.stats[self.rain_nick])
    self.assertTrue(stats is self.stats[self.rain_nick])


  def test_generate_nonrandom_unknown(self):

    self.users_instance.getRealNicks.return_value = []

    self.generator.init(self.users_instance, {}, 0)
    nicks, quote = self.generator.generate([])

    self.assertFalse(nicks)
    self.assertFalse(quote)


  def test_generate_nonrandom_known_single_short(self):

    nick_tuples = [(users.UserNickType.NONRANDOM, self.saoi_nick)]

    self.users_instance.getRealNicks.return_value = [self.saoi_nick]
    self.users_instance.getStarters.side_effect = self.starters_side_effect
    self.users_instance.getGenericLookbacks.return_value = []

    self.generator.init(self.users_instance, {}, 0)
    nicks, quote = self.generator.generate(nick_tuples)

    self.assertEqual(len(nicks), 1)
    self.assertEqual(nicks[0], self.saoi_nick)
    self.assertEqual(quote, ' '.join(list(self.starters[self.saoi_nick][0])))


  def test_generate_nonrandom_known_single(self):

    nick_tuples = [(users.UserNickType.NONRANDOM, self.saoi_nick)]

    self.users_instance.getRealNicks.return_value = [self.saoi_nick]
    self.users_instance.getStarters.side_effect = self.starters_side_effect
    self.users_instance.getGenericLookbacks.side_effect = self.generic_lookbacks_side_effect

    self.generator.init(self.users_instance, {}, 0)
    nicks, quote = self.generator.generate(nick_tuples)

    self.assertEqual(len(nicks), 1)
    self.assertEqual(nicks[0], self.saoi_nick)
    self.assertEqual(quote, self.quotes[self.saoi_nick])


  def test_generate_nonrandom_known_multiple(self):

    nick_tuples = [
      (users.UserNickType.NONRANDOM, self.saoi_nick),
      (users.UserNickType.NONRANDOM, self.file_nick),
    ]

    self.users_instance.getRealNicks.return_value = [self.saoi_nick, self.file_nick]
    self.users_instance.getStarters.side_effect = self.starters_side_effect
    self.users_instance.getGenericLookbacks.side_effect = self.generic_lookbacks_side_effect

    self.generator.init(self.users_instance, {}, 0)
    nicks, quote = self.generator.generate(nick_tuples)

    self.assertTrue(nicks)
    self.assertEqual(len(nicks), 2)
    self.assertTrue(self.saoi_nick in nicks)
    self.assertTrue(self.file_nick in nicks)
    possible_quotes = [self.quotes[self.saoi_nick], self.quotes[self.bard_nick]]
    self.assertTrue(quote in possible_quotes)


  def test_generate_nonrandom_known_parentheses(self):

    nick_tuples = [(users.UserNickType.NONRANDOM, self.bard_nick)]

    self.users_instance.getRealNicks.return_value = [self.bard_nick]
    self.users_instance.getStarters.side_effect = self.starters_side_effect
    self.users_instance.getGenericLookbacks.side_effect = self.generic_lookbacks_side_effect
    self.users_instance.getClosingLookbacks.side_effect = self.closing_lookbacks_side_effect

    self.generator.init(self.users_instance, {}, 0)
    nicks, quote = self.generator.generate(nick_tuples)

    self.assertEqual(len(nicks), 1)
    self.assertEqual(nicks[0], self.bard_nick)
    self.assertEqual(quote, self.quotes[self.bard_nick])


if __name__ == "__main__":
  unittest.main()

