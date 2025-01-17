# romaAI
RL to play American checkers;
The used stack is Python + pyimgui(imgui[glfw]) + NumPy

#### The rules of American checkers ([YT video](https://youtu.be/ScKIdStgAfU)):
1. Board size is 6x6
2. Light colored square in the right bottom corner
3. Checkers are placed on the dark squares
4. The game goes until one of the players has no more moves
5. Simple checkers can only move forward diagonally
6. More than one capture can be made during the move
7. If a capture is possible, it must be made
8. If a checker reaches the opposite side of the board, it becomes a king
9. Kings can move and capture diagonally in both directions

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