import random
from abc import ABC, abstractmethod
from typing import Callable
from os import PathLike

from .board import Board, GameState

class IPlayer(ABC):
	@abstractmethod
	def decide_move(self, board: Board) -> tuple[tuple[int, int], tuple[int, int]]:
		pass

	def do_round(self, enemy: 'IPlayer') -> bool:
		board = Board()
		while True:
			if board.game_state != GameState.NOT_OVER:
				return board.game_state == GameState.POSITIVE_WINS
			s, e = self.decide_move(board)
			board.make_move(s, e)

			if board.game_state != GameState.NOT_OVER:
				return board.game_state == GameState.POSITIVE_WINS
			s, e = enemy.decide_move(board)
			board.make_move(s, e)

class UserInput(IPlayer):
	def decide_move(self, board: Board) -> tuple[tuple[int, int], tuple[int, int]]:
		raise NotImplementedError("Should be handled by UI side")

	def __str__(self) -> str:
		return "User input"
	

class IRandomPlayer(IPlayer):
	def __save_random_state(self, func: Callable) -> Callable:
		def wrapper(*args, **kwargs):
			self.random.seed(self.seed)
			res = func(*args, **kwargs)
			self.seed = self.random.randint(0, 1<<16 - 1)
			return res
		return wrapper

	def __init__(self, seed: int) -> None:
		super().__init__()

		self.decide_move = self.__save_random_state(self.decide_move)

		self.seed = seed
		self.random = random.Random(seed)
	
class RandomPlayer(IRandomPlayer):
	def __init__(self, seed: int = 0) -> None:
		super().__init__(seed)

	def decide_move(self, board: Board) -> tuple[tuple[int, int], tuple[int, int]]:
		possible_starts = list(board.get_possible_pos())
		self.random.shuffle(possible_starts)

		for start in possible_starts:
			possible_ends_gen = board.get_correct_moves(start)
			first_end = next(possible_ends_gen, None)
			if not first_end:
				continue
			end = self.random.choice([first_end] + list(possible_ends_gen))
			return start, end
		
		raise ValueError("Tried to ask for a move when there are no possible moves")

	def __str__(self) -> str:
		return "Random player"
	
class ITrainablePlayer(IPlayer):
	@abstractmethod
	def do_training_round(self, enemy: 'IPlayer', sign: int) -> bool:
		"""Returns true if the model won the game"""
		return False
	
	@abstractmethod
	def save_model(self, path: PathLike | str) -> None:
		pass

	@abstractmethod
	def load_model(self, path: PathLike | str) -> None:
		pass

class IParallelTrainablePlayer(ITrainablePlayer):
	@staticmethod
	@abstractmethod
	def join(models: list['IParallelTrainablePlayer']) -> 'IParallelTrainablePlayer':
		pass