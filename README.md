WordFeudCheater
===============
This work is based on the excellent and efficient scrabble solver from [astralcai](https://github.com/astralcai/scrabbler/tree/master).

[WordFeud](https://wordfeud.com/) is a scrabble game for your mobile. My Fiance has been killing me in almost every game.

_What's a hacker to do but write some code that can make it a more even fight!_

WordFeudCheater will propose the next move in a wordfeud.

It does this using OCR to identify the tiles placed on the board and in the rack.

Simply take a screenshot and Airdrop it to your Mac.

The code checks for new screenshots (IMG_*.jpeg) every 10 seconds in your ~/Downloads directory.

When found will, it moves it into the images directory, analyzes the board and will propose several next moves.

### Notes:

* Works on my phone, not sure if it will work on yours because of different screenshot sizes based on your phone.

### ToDo:
- Emulate the competitor, by playing the next move after yours to see what possible follow up scores they could get.
- Add a Graphical Front End using pygame.