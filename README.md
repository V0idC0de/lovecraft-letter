# Lovecraft Letter - CLI Edition

This is an implementation of the game "Lovecraft Letter" by Seiji Kanai, using the CLI for input and output.

Since seeing your opponents cards in the logs makes the game basically pointless, this is more of a proof of concept,
than an implementation you can play with anyone.

This was developed as a Python exercise because I felt like implementing some game logic and I'm happy with 
how it looks right now.

In the future, I might consider one or more of the following:

1. Bring English card names and effect texts into the game (I started with German, but switched to English out of habit
when writing log messages, etc.)
2. Implement some CPU-opponents to play against
2. Implement a GUI using `tkinter`, which was the initial idea, but I got obsessed with the game logic instead (lol)
3. Make this playable via network, by utilizing some sort of messaging system (GCP PubSub maybe?)

> I wrote the Game Engine in a way that allows for easy extension with more made-up cards or tweaking of effects.
> Cards are defined in `card.py` and consist of one or more `Effect` objects, that handle the actual card effects.

**Anybody could ...**

1. add new effects in `effect.py`
2. tweak existing effects or cards
3. edit the deck this game is played with, by editing `deck.txt`
4. implement some of my ideas above

## Usage

1. Clone this repository
2. Change to the root directory of the repository
3. [Optional] Create a `venv` by running `python -m venv venv`
   1. After that, you should enable the `venv` by running `source venv/bin/activate` on Linux 
      or `venv\Scripts\activate.bat` on Windows
4. Install the requirements with `pip install -r requirements.txt`
5. Run `python main.py` in the root directory

> Using the `Gamestate` creation in `main.py` you can pass either a number of players or a list of player names.
> Just change `gamestate.Gamestate()` to `gamestate.Gamestate(3)` or `gamestate.Gamestate(["Alice", "Bob", "Charlie"])`.
> You can use any number of players, however there is no failsafe against too many players.
