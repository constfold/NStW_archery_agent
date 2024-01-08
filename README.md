# NStW reversing
Reversing of the game "Nobody Saves The World" by Drinkbox Studios just for fun.

The game is written in a proprietary engine called "Drinkbox Engine 2D" and uses the GameMonkey Script for scripting.

## Extracting scripts & resources
```
python main.py extract -i levels.dat
python main.py extract -i misc.dat
python main.py extract -i resources.dat
```

## Scripts modding
First generate the patched version of the scripts.
```
compilegm patch.gm patch.gmb
python main.py patch levels.gmb patch.gmb modded.gmb
```
Then inject the `modded.gmb` file into game.
```
launch_with NtSW.exe mod.dll
```
