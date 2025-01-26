from board import Board, GameState
import copy

arr: set[bytes] = set()
b = Board()
q: list[tuple[bytes, Board]] = [(bytes(b), b)]
prev_max = 0

while q:
	cur_bytes, cur = q.pop()
	arr.add(cur_bytes)

	if cur.game_state != GameState.NOT_OVER:
		continue

	for start in cur.get_possible_pos():
		for end in cur.get_correct_moves(start):
			new_board = copy.deepcopy(cur)
			new_board.make_move(start, end)
			new_board_bytes = bytes(new_board)

			if new_board_bytes in arr:
				continue

			q.append((new_board_bytes, new_board))
	
	l = len(arr)
	if l % 1e3 == 0 and l > prev_max:
		print(l)
		prev_max = l

print(len(arr))
