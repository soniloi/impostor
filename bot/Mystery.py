import random


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


  def getDescription(self):

    description = "The mystery author says: [" + self.quotes[0] + "]"
    for quote in self.quotes[1:]:
      description += " and [" + quote + "]"
    description += ". "

    if self.nick_characters:
      description += "Their nick contains the character(s) ["
      description += ",".join(self.nick_characters)
      description += "]. "

    if self.already_guessed:
      description += "The nick(s) guessed so far are ["
      description += ",".join(self.already_guessed)
      description += "]. "

    return description


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

