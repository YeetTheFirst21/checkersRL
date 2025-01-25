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
8. Kings can move and capture diagonally in all directions ONE STEP <- that's a small rule update from [here](https://checkers.online/magazine/game/american-checkers-rules#:~:text=A%20king%20in,backward%20one%20square)

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