import numpy as np

from abc import ABC, abstractmethod

class IPlayer(ABC):
	@abstractmethod
	def decide_move(self, board: np.ndarray[tuple[int, int], np.dtype[np.int8]], sign: int) -> tuple[tuple[int, int], tuple[int, int]]:
		pass

class UserInput(IPlayer):
	def decide_move(self, board: np.ndarray[tuple[int, int], np.dtype[np.int8]], sign: int) -> tuple[tuple[int, int], tuple[int, int]]:
		raise NotImplementedError("Should be handled by UI side")

	def __str__(self) -> str:
		return "User input"