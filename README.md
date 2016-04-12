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

You will need source material for each user. These must all be located in the same directory, using the following format:

* Plain text files, each with the extension ```.src```.
* Each line of input is to be on its own line in the file.
* Each line is to have at least two words.

Lastly, there should be one source file named ```all.src```. This should be an amalgamation of all users in the data-set. Hopefully, there will be no-one with the username ```all```!

The location of this directory does not matter; the directory name will be passed at run-time (see below). How the source material is generated is up to you. Typically, it will involve parsing IRC log files, stripping out very short lines, and maybe some normalization.

Note that the more input (both number of lines and number of words per line) we have for a user, the better the output will be. The generator works best when there are many possible successors to each pair of words; the more possible successors, the more varied the generated lines.

## Example

Say we have a user with username ```mollusc```. In our sources directory there must be a file named ```mollusc.src```. Its contents could be something like this:

```
I am not a fish
my occupation is making pearls
om nom nom tasty algae
today is not a good day
```

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

The trigger for the ```impostor``` bot is the character '!'. The bot will ignore any line that does not start with this symbol.

Other than ```all```, the words that may not appear as usernames are:

* ```impostor```: calling this returns usage information in-channel.
* ```random```: calling this returns a random-user comment.

Note that, if the source material contains reserved usernames, then they will be overridden by the above functions. Again, hopefully, there will be no-one with these usernames.

### Single-user comment

A single-user comment is one generated from the source material of only one user. To generate a single-user comment for a user named ```mollusc```, type the following in the ```impostor``` channel:
```
!mollusc
```

### Multi-user comment

A multi-user comment is one generated from the source material of multiple users; it is currently limited to to users. To generate such a comment for users ```mollusc``` and ```daffodil```, type:
```
!mollusc:daffodil
```

The ordering does not matter; reversing it to ```!daffodil:mollusc``` will produce exactly the same results.

### Random-user comment

A random-user comment is one generated from a random single user in the set. To generate such a comment, type:
```
!random
```
