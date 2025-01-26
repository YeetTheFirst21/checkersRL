# romaAI
RL to play American checkers;
The used stack is Python (3.10+) + pyimgui(imgui[glfw]) + NumPy

#### The rules of American checkers ([YT video](https://youtu.be/ScKIdStgAfU)) ([a better rule source](https://checkers.online/magazine/game/american-checkers-rules)):
1. Board size is 6x6
2. Light colored square in the right bottom corner
3. Checkers are placed on the dark squares
4. The game goes until one of the players has no more moves
5. Simple checkers can only move forward diagonally one step
6. All possible captures must be made during the turn
7. If a checker reaches the opposite side of the board, it becomes a king
8. TODO: this rule should probably be cancelled. Kings can move and capture diagonally in all directions ONE STEP <- that's a small rule update from [here](https://checkers.online/magazine/game/american-checkers-rules#:~:text=A%20king%20in,backward%20one%20square)

#### Implementation details:
Board is represented as a 6x6 NumPy array, where
* `2` - king positive checker
* `1` - simple positive checker
* `0` - empty square
* `-1` - simple negative checker
* `-2` - king negative checker
```python
self.board = np.array([
	[-1, 0, -1, 0, -1, 0],
	[0, -1, 0, -1, 0, -1],
	[0, 0, 0, 0, 0, 0],
	[0, 0, 0, 0, 0, 0],
	[1, 0, 1, 0, 1, 0],
	[0, 1, 0, 1, 0, 1]
]).T
```

#### Fixing the autocomplete issue with pyimgui
The following extension could be used to *Create Cython TypeStub for Python* from the `.pyx` files of the library:

https://marketplace.visualstudio.com/items?itemName=ktnrg45.vscode-cython


## Documenting different approaches
### Brute force
After running the state discovery code for 7.5m the amount of discovered states went over 1.01e6, taking up around 90MB of RAM while running in one thread.

An approximate estimation of number of possible states (not taking into account the lower number of pieces is compensated by taking into account the unreachable states):

$$\displaystyle \frac{18!}{12!\cdot6!}\cdot2^{12}\approx76\cdot10^6$$

It gives an estimation that the memory and time usage should be increased by around 70x just to enumerate all the states. This is not feasible, thus the brute force approach is not applicable.