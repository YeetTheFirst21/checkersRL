import numpy as np

from abc import ABC, abstractmethod

from .board import Board

class IPlayer(ABC):
	@abstractmethod
	def decide_move(self, board: Board, sign: int) -> tuple[tuple[int, int], tuple[int, int]]:
		pass

class UserInput(IPlayer):
	def decide_move(self, board: Board, sign: int) -> tuple[tuple[int, int], tuple[int, int]]:
		raise NotImplementedError("Should be handled by UI side")

	def __str__(self) -> str:
		return "User input"
	
class RandomPlayer(IPlayer):
	def decide_move(self, board: Board, sign: int) -> tuple[tuple[int, int], tuple[int, int]]:
		raise NotImplementedError("TODO")

	def __str__(self) -> str:
		return "Random player"