from sortedcontainers import SortedList

import copy
import concurrent.futures
import pickle
import time
from dataclasses import dataclass
from typing import Optional
from concurrent.futures import Future

from board import Board, GameState

OUR_SIGN = -1

@dataclass
class LeafData:
	depth: int
	board_bytes: bytes
	game_state: GameState
	turn_sign: int
	parent_bytes: Optional[bytes]
	children_bytes: Optional[list[bytes]]
	stats: dict[bool, int]
	completed: bool

	def __post_init__(self):
		self.__value = None
		self.__hash = None

	def __compute_int(self):
		ret = 0
		board = Board.from_num_repr(self.board_bytes)
		for _, piece in board:
			ret += piece * OUR_SIGN
		
		ret *= 5
		ret += self.depth // (board.moves_since_last_capture + 1)

		if board.turn_sign != OUR_SIGN:
			ret = -ret

		del board
		return ret
	
	@property
	def value(self) -> int:
		if not self.__value:
			self.__value = self.__compute_int()
		return self.__value
	
	def __hash__(self) -> int:
		if not self.__hash:
			self.__hash = hash(self.board_bytes)
		return self.__hash


def process_board(leaf: LeafData) -> list[LeafData]:
	ret = []
	board = Board.from_num_repr(leaf.board_bytes)
	for start in board.get_possible_pos():
		for end in board.get_correct_moves(start):
			new_board = copy.deepcopy(board)
			new_board.make_move(start, end)

			new_leaf = LeafData(
				leaf.depth + 1,
				bytes(new_board),
				new_board.game_state,
				new_board.turn_sign,
				leaf.board_bytes,
				None,
				{False: 0, True: 0},
				new_board.game_state != GameState.NOT_OVER
			)
			if new_leaf.completed:
				new_leaf.stats[new_leaf.game_state == GameState(OUR_SIGN)] += 1
			ret.append(new_leaf)
	
	return ret


if __name__ == "__main__":
	executor = concurrent.futures.ProcessPoolExecutor(max_workers=8)
	root_board = Board()
	root = LeafData(
		0,
		bytes(root_board),
		root_board.game_state,
		root_board.turn_sign,
		None,
		None,
		{False: 0, True: 0},
		False
	)
	leaf_dict = {root.board_bytes: root}
	jobs: list[Future[list[LeafData]]] = []
	pending_leafs = SortedList([root], key=lambda x: x.value)
	depths = {}
	prev_len = 0
	completed = 0

	try:
		while jobs or pending_leafs:
			while len(jobs) < 8 and pending_leafs:
				leaf: LeafData = pending_leafs.pop()
				if leaf.completed or (
					leaf.parent_bytes and leaf_dict[leaf.parent_bytes].completed
				):
					continue
				jobs.append(executor.submit(process_board, leaf))

			last_job = jobs.pop()

			leafs = last_job.result()
			assert leafs[0].parent_bytes

			parent_leaf = leaf_dict[leafs[0].parent_bytes]
			parent_leaf.children_bytes = [
				leaf.board_bytes for leaf in leafs
			]
			depths[parent_leaf.depth] = depths.get(parent_leaf.depth, 0) + 1

			for leaf in leafs:
				if parent_leaf.completed:
					break

				if leaf.game_state == GameState.NOT_OVER:
					leaf_dict[leaf.board_bytes] = leaf
					pending_leafs.add(leaf)
				
				else:
					completed += 1
					res = leaf.game_state == GameState(OUR_SIGN)
					parent = leaf
					while parent.parent_bytes:
						parent = leaf_dict[parent.parent_bytes]

						parent.stats[res] += 1
						if parent.children_bytes:
							parent.completed = all(
								child in leaf_dict and leaf_dict[child].completed
								for child in parent.children_bytes
							)
							if not parent.completed:
								if parent.turn_sign == OUR_SIGN:
									parent.completed = any(
										child in leaf_dict and 
										leaf_dict[child].completed and 
										leaf_dict[child].stats[False] == 0
										for child in parent.children_bytes
									)
								else:
									parent.completed = any(
										child in leaf_dict and 
										leaf_dict[child].completed and 
										leaf_dict[child].stats[True] == 0
										for child in parent.children_bytes
									)

			l = len(leaf_dict)
			if l - prev_len > 5e2:
				prev_len = l
				print(l, len(pending_leafs), completed, time.strftime("%H:%M:%S"), depths)
				with open("tree.pickle", "wb") as f:
					pickle.dump(leaf_dict, f)
	finally:
		with open("tree.pickle", "wb") as f:
			pickle.dump(leaf_dict, f)

	print(len(leaf_dict))
