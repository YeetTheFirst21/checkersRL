import copy
import concurrent.futures
import pickle
import time

from board import Board, GameState


def process_board(board_int: int, board: Board, depth: int) -> tuple[int, list[tuple[int, Board]], int]:
	possible_moves: list[tuple[int, Board]] = []
	for start in board.get_possible_pos():
		for end in board.get_correct_moves(start):
			new_board = copy.deepcopy(board)
			new_board.make_move(start, end)
			possible_moves.append((int(new_board), new_board))
	
	return board_int, possible_moves, depth

if __name__ == "__main__":
	executor = concurrent.futures.ProcessPoolExecutor(max_workers=8)
	root_board = Board()
	jobs = [executor.submit(process_board, int(root_board), root_board, 0)]
	parent_tree: dict[int, set[int]] = {}
	depths: dict[int, int] = {}
	prev_len = 0

	while jobs:
		last_job = jobs.pop()

		parent_board_int, possible_moves, depth = last_job.result()
		depths[depth] = depths.get(depth, 0) + 1
		for child_board_int, child_board in possible_moves:
			if child_board_int in parent_tree:
				parent_tree[child_board_int].add(parent_board_int)
				continue

			parent_tree[child_board_int] = {parent_board_int}

			if child_board.game_state == GameState.NOT_OVER:
				jobs.append(executor.submit(process_board, child_board_int, child_board, depth + 1))

		l = len(parent_tree)
		if l - prev_len > 5e4:
			prev_len = l
			print(len(parent_tree), len(jobs), time.strftime("%H:%M:%S"), depths)
			with open("parent_tree.pickle", "wb") as f:
				pickle.dump(parent_tree, f)

	print(len(parent_tree))
