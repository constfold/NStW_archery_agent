# NStW reversing
Reversing of the game "Nobody Saves The World" by Drinkbox Studios just for fun.

The game is written in a proprietary engine called "Drinkbox Engine" and uses the GameMonkey Script for scripting.

I create this repository basically for myself to solve a boring minigame in the game.
I'm willing to make fun of that minigame, but for now it is just about some linear equtions about velocity.

## Extracting scripts & resources
```sh
python main.py extract -i levels.dat
python main.py extract -i misc.dat
python main.py extract -i resources.dat
```

## Scripts modding
First generate the patched version of the scripts.
```sh
compilegm patch.gm patch.gmb
python main.py patch levels.gmb patch.gmb patch_.gmb
```
Then inject the `patch_.gmb` file into game.
```sh
withdll -d:worker.dll NtSW.exe 
```
