from collections import namedtuple

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

    hint = None

    if self.future_hints:
      hint = self.future_hints[0]

      if hint[0] == HintType.NICK_CHARACTER:
        self.nick_characters.append(hint[1])

      elif hint[0] == HintType.ADDITIONAL_QUOTE:
        self.quotes.append(hint[1])

      del self.future_hints[0]

    return hint


  # Evaluate a guess, with aliasing
  # Return the original (real) nick if correct, or None if incorrect
  def guess(self, guess):
    self.already_guessed.add(guess)
    if guess == self.author or guess in self.author_aliases:
      return self.author
    return None

