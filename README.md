# NStW Archery Agent
An agent to solve the archery minigame in Nobody Saves the World by Drinkbox Studios.

## Agent
I plan to implement agents with following various techniques just for fun.

- [X] Rule-based, with a priori knowledge on when/how targets move
- [ ] Rule-based, but doesn't know the accurate information about targets' speed and trail
- [ ] Reinforcement Learning, with position as states
- [ ] Reinforcement Learning, but only image/graphic input

## Resource Unpacking
The unpacking scripts are in `main.py`, and its usage as follows:

```sh
python main.py extract -i levels.dat
python main.py extract -i misc.dat
python main.py extract -i resources.dat
```

## Scripts modding
NStW uses the GameMonkey Script for scripting. Here's a tutorial on how to modding.

- Firstly, generate the patched version of the scripts.
```sh
compilegm patch.gm patch.gmb
python main.py patch levels.gmb patch.gmb patch_.gmb
```

- Then, inject the `patch_.gmb` file into game.
```sh
withdll -d:worker.dll NtSW.exe 
```
