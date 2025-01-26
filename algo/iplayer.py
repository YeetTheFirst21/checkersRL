import numpy as np

import random
from abc import ABC, abstractmethod

from .board import Board, _s

class IPlayer(ABC):
	@abstractmethod
	def decide_move(self, board: Board) -> tuple[tuple[int, int], tuple[int, int]]:
		pass

class UserInput(IPlayer):
	def decide_move(self, board: Board) -> tuple[tuple[int, int], tuple[int, int]]:
		raise NotImplementedError("Should be handled by UI side")

	def __str__(self) -> str:
		return "User input"
	
class RandomPlayer(IPlayer):
	def __init__(self, seed: int) -> None:
		super().__init__()
		self.seed = seed

	def decide_move(self, board: Board) -> tuple[tuple[int, int], tuple[int, int]]:
		random.seed(self.seed)

		possible_starts = list(board.get_possible_pos())
		random.shuffle(possible_starts)

		for start in possible_starts:
			possible_ends = board.get_correct_moves(start)
			if not possible_ends:
				continue
			end = random.choice(list(possible_ends))
			return start, end
		
		raise ValueError("Tried to ask for a move when there are no possible moves")

	def __str__(self) -> str:
		return "Random player"