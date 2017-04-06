# impostor

This is an IRC bot that generates individualized Markov chains based on given source material. It can be used, for example, to generate 'new' phrases from a user based on things they have said before. It is written in python, using the Twisted framework.

## Example

Take a user with the following input set:
```
she sells sea-shells by the sea-shore
the dog was eating sausages by the dozen
```

The following are the possible outputs:
```
she sells sea-shells by the sea-shore
she sells sea-shells by the dozen
the dog was eating sausages by the dozen
the dog was eating sausages by the sea-shore
```

# Dependencies

* Python: tested with version 2.7.9, other versions of Python 2.x may also work
* python-twisted: tested with version 14.x, other versions may also work

# Pre-requisites

There must be a single input directory, containing the items listed below. The location of this directory does not matter; the directory name will be passed at run-time.

## Source material files

These are plain text files, each with the extension ```.src```. The filename minus the extension is the username. The following format must apply.
* Each line of input is to be on its own line in the file.
* Each line is to have at least two words.
* If there is a source file that is an amalgamation of all source files, call it ```all.src```

How the source material is generated is up to you. Typically, it will involve parsing IRC log files, stripping out very short lines, and maybe some normalization.

Note that the more input (both number of lines and number of words per line) we have for a user, the better the output will be. The generator works best when there are many possible successors to each pair of words; the more possible successors, the more varied the generated lines.

### Sample source material file

Say we have a user with username ```mollusc```. In our sources directory there must be a file named ```mollusc.src```. Its contents could be something like this:

```
I am not a fish
my occupation is making pearls
om nom nom tasty algae
today is not a good day
```

## Metadata

An optional file called ```meta.info``` may be added to the input directory. If present, this would contain metadata about source generation. The following attributes are supported.
* Date: Unix timestamp of when the source material was generated.
* Primary: The primary channel used to generate source material.
* Additional: Other channels from which source material is taken (one may wish, for example, to exclude users found in the additional channels but not in the primary).

### Sample metadata file

```
date=1489964352
primary=#underthesea
additional=#mollusc_test #beach #iloveraisins
```

## User merge information

An optional file called ```merge.lst``` may be added to the input directory. If present, this would contain mappings of user aliases (other nicks a user has been known by) to canonical nicknames. The file should be laid out as follows.
* Each user must be on its own line.
* Lines consist of tab-separated nicks.
* The first nick is the canonical one; all other nicks are aliases.

# Running

## Starting

From the checkout location, run
```
export PYTHONPATH=$(pwd):$PYTHONPATH
python impostor/ImpostorBot.py <network> <channel> <logfile> <sourcedir>
```

Where

* ```<network>``` is the name of the network the bot is to connect to, e.g. ```irc.freenode.net```.
* ```<channel>``` is the name of the channel the bot is to run in, e.g. ```#impostor```.
* ```<logfile>``` is the name of the file that the bot is to log to while it is running.
* ```<sourcedir>``` is the location of the directory containing all of the source material.

By default, the bot will connect with the nick ```impostor```. If this is taken, it will instead use ```impostor^``` by default. If this, too, is taken, then it will fail.

Note that, if there is a lot of source material, it may take a few seconds to start.

## Usage

The instructions below indicate what to type in IRC to prompt the bot. First, you must connect to IRC as usual and join the channel the bot is in.

### Reserved characters and usernames

There are two triggers for the ```impostor``` bot, ```!``` and ```@```. One can also direct a comment at the bot by starting a line with ```impostor:```, but all this does is display a help message. The bot ignores all other lines.

The only reserved username (other than ```all```, if present) is ```random```. If there is a user called ```random```, then it will not be possible to generate lines for them. Everything else is possible though; one can even call ```impostor``` on itself.

### Generating quotes

The trigger to generate quotes is ```!```.

#### Single-user comment

A single-user comment is one generated from the source material of only one user. To generate a single-user comment for a user named ```mollusc```, type the following in the ```impostor``` channel:
```
!mollusc
```

#### Multi-user comment

A multi-user comment is one generated from the source material of multiple users; it is currently limited to two users. To generate such a comment for users ```mollusc``` and ```daffodil```, type:
```
!mollusc:daffodil
```

The ordering does not matter; reversing it to ```!daffodil:mollusc``` will produce exactly the same results.

#### Random-user comment

A random-user comment is one generated from a random user in the set. To generate such a comment, type:
```
!random
```

```random``` may be substituted anywhere a normal nick is expected. In other words, the following are all valid.
```
!mollusc:random
!random:mollusc
!random:random
```

#### Notes

If the bot is called on a username that does not exist, then it does not do anything.

If the bot is called on a nick that is an alias, then the real user will be resolved.

If it is called for a combination of a user that exists and one that does not, then it will only return a quote for one that exists.

If ```random``` is called as part of a combination (including a ```random:random``` combination), it will not return two of the same.

### Additional features

Other features are triggered using the ```@``` trigger.

#### Help

To see a help message, type:
```
@help
```

#### Statistics

To see some channel statistics (and other, non-statistical, information), type:
```
@stats
```

To see some statistics pertaining to a specific user, type:
```
@stats <nick>
```

#### Mystery game

This is a simple game where players guess the identity (or "author") of a Markov-generated quote. It is controlled using the following commands.

To start a game, type:
```
@mystery
```
```impostor``` will print a generated quote from some random user. Users with fewer than a certain number of source productions are excluded. This is in order to avoid huge numbers of quotes from little-known, unguessable users. 

Players then attempt to guess the identity of the author, by typing:
```
@guess <nick>
```
Players can guess as many times as they like. It is also possible to request hints:
```
@hint
```
This will print a character from the author's name at random. Up to three hints may be requested. If the nick consists of three characters or fewer, only one hint will be given. To see the solution, type:
```
@solve
```
The game ends when either someone guesses correctly, or ```@solve``` is called. There are no prizes.
