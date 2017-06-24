from collections import namedtuple
import random

MysteryInfo = namedtuple("MysteryInfo", "known_quotes known_nick_characters already_guessed")


class HintType:
  NICK_CHARACTER = 0
  ADDITIONAL_QUOTE = 1


class Mystery:

  def __init__(self, ident, author, author_aliases, initial_quote, hints):
    self.ident = ident
    self.author = author
    self.author_aliases = author_aliases
    self.quotes = [initial_quote]
    self.nick_characters = []
    self.future_hints = hints
    self.already_guessed = set()


  def getInfo(self):

    return MysteryInfo(
      self.quotes,
      self.nick_characters,
      self.already_guessed
    )


  def getHint(self):

    hint_message = ""

    if not self.future_hints:
      hint_message = "I have no further hints to give. "

    else:
      hint_index = random.randint(0, len(self.future_hints) - 1)
      (hint_type, hint) = self.future_hints[hint_index]
      del self.future_hints[hint_index]

      if hint_type == HintType.NICK_CHARACTER:
        self.nick_characters.append(hint)
        hint_message = "The mystery author's name contains the character [" + hint + "]"

      elif hint_type == HintType.ADDITIONAL_QUOTE:
        self.quotes.append(hint)
        hint_message = "The mystery author also says: [" + hint + "]"

    return hint_message


  # Evaluate a guess, with aliasing
  # Return the original (real) nick if correct, or None if incorrect
  def guess(self, guess):
    self.already_guessed.add(guess)
    if guess == self.author or guess in self.author_aliases:
      return self.author
    return None

