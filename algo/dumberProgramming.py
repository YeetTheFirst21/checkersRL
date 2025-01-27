from . import iplayer

import random
import math
from .board import Board, _s
import numpy as np

import pickle

class dumberPlayer(iplayer.IPlayer):
	
	# here is a dictionary we have, the first keys are the states of the game and the second keys are the moves that can be made from that state and then finally the value of the moves that can be max 100.
	"""
	{
		(
			board_config,
			turn_sign,
			from,
			to
		):
		value
	}
	"""
	mem_key_type = tuple[int, int, tuple[int, int], tuple[int, int]]
	memoryArr: dict[mem_key_type, float] = {}
	
	# here is how a game board usually looks like:
		# 	self.__board: np.ndarray[tuple[int, int], np.dtype[np.int8]] = np.array([
		# 	[-1, 0, -1, 0, -1, 0],
		# 	[0, -1, 0, -1, 0, -1],
		# 	[0, 0, 0, 0, 0, 0],
		# 	[0, 0, 0, 0, 0, 0],
		# 	[1, 0, 1, 0, 1, 0],
		# 	[0, 1, 0, 1, 0, 1]
		# ], dtype=np.int8).reshape(self.SIZE, self.SIZE).T
	
	def __init__(self,startFresh:bool = False, seed:int=0):
		super().__init__()
		self.seed = seed
		if startFresh:
			# since we are doing a fresh start, we will create a new memory array full of all possible states and moves and give them a value of 100.
			# we get a new Board object to get the possible states and moves.
			# we always assume for this board that the player is positive and the enemy is negative.
			board = Board()
		else:
			# we will load the memory array from the file.
			self.loadTraining("")
		
	def __get_exponent(self, startingPointIntValue: int, turn_sign: int, start: tuple[int, int], end: tuple[int, int]) -> float:
		key = (startingPointIntValue, turn_sign, start, end)
		if key not in self.memoryArr:
			# print("miss")
			return 1.
		else:
			# print("hit")
			try:
				return math.exp(self.memoryArr[key])
			except:
				return 1.

	def decide_move(self, board: iplayer.Board) -> tuple[tuple[int, int], tuple[int, int]]:
		turn_sign = board.turn_sign
		possible_moves: dict[tuple[int, int], tuple[int, int]] = []
		for start in board.get_possible_pos():
			startingPointIntValue = board[start]
			for end in board.get_correct_moves(start):
				startingPointIntValue = board[start]
				possible_moves.append(
					(
						self.__get_exponent(startingPointIntValue, turn_sign, start, end),
						(start, end)
					)
				)
		

		exponents, moves = zip(*possible_moves)
		random.seed(self.seed)
		r = random.random() * sum(exponents)
		self.seed = random.randint(0, 1000000)
		for i, move in enumerate(moves):
			r -= exponents[i]
			if r <= 0:
				return move
		
		raise ValueError("Tried to ask for a move when there are no possible moves")

	def do_training_step(self, enemy: iplayer.IPlayer, bot_sign: int):
		# this is pretty much the same as decide_move but we will also update the memory array if we lose or win.
		# we will get the best move from the memory array and then play it.
		
		# creating initial board to start the game:
		board = Board()
		# we assume the enemy starts first.
		# we will play the game until it ends while saving all the moves we make in:
		movesMade = set()
		# this will hold the board,start,end and with it at the end we will update the memory array by incrementing all the moves that led to a win by 1 and decrementing all the moves that led to a loss by 1.	

		def player_order():
			if bot_sign == 1:
				while True:
					yield self
					yield enemy
			else:
				while True:
					yield enemy
					yield self

		# we will play the game until it ends:
		for player in player_order():
			start,end = player.decide_move(board)
			startingPointIntValue = board[start]

			movesMade.add((startingPointIntValue, board.turn_sign, start, end))
			board.make_move(start,end)
			if board.game_state.value != 0:
				break
		
		abs_delta = 3 * 0.9 ** len(movesMade)
		if board.game_state.value != -2:
			#print(f"state:{board.game_state.value==bot_sign}")
			delta = _s(board.game_state.value) * bot_sign * abs_delta
			for move in movesMade:
				if move not in self.memoryArr:
					self.memoryArr[move] = 0
				self.memoryArr[move] += delta * move[1]
		else:
			for move in movesMade:
				if move not in self.memoryArr:
					self.memoryArr[move] = 0
				self.memoryArr[move] -= (abs_delta/2)
		# we will save the memory array to a file:
		# self.saveTraining("")
	
	def saveTraining(self, path: str) -> None:
		path = path or "dynamic_learning_agent"
		with open(path+".DUMBdynamicProgrammingSave", "wb") as f:
			pickle.dump(self.memoryArr, f)
			
	def loadTraining(self, path: str) -> bool:
		path = path or "dynamic_learning_agent"
		try:
			with open(path+".DUMBdynamicProgrammingSave", "rb") as f:
				self.memoryArr = pickle.load(f)
			return True
		except FileNotFoundError:
			return False
	
	@staticmethod
	def combine(*agents: iplayer.IPlayer) -> 'dumberPlayer':
		combined = dumberPlayer()
		for agent in agents:
			assert isinstance(agent, dumberPlayer)
			for key, value in agent.memoryArr.items():
				if key not in combined.memoryArr:
					combined.memoryArr[key] = 0
				combined.memoryArr[key] += value
		return combined

	def __str__(self) -> str:
		return "Dumb Learning Agent"
	