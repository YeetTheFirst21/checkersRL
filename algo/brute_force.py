from board import Board, GameState

arr = set()
q = [int(Board())]

while q:
	cur = q.pop()
	cur_b = Board.from_num_repr(cur)
	if cur in arr:
		continue
	arr.add(int(cur))
	for start in cur_b.get_possible_pos():
		for end in cur_b.get_correct_moves(start):
			new_board = Board.from_num_repr(cur)
			new_board.make_move(start, end)
			if new_board.game_state == GameState.NOT_OVER:
				q.append(int(new_board))
	
	if len(arr) % 1e3 == 0:
		print(len(arr))

print(len(arr))
