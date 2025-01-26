from . import iplayer

import random
from .board import Board, _s
import numpy as np

import pickle

class dynamicPlayer(iplayer.IPlayer):
	
	# here is a dictionary we have, the first keys are the states of the game and the second keys are the moves that can be made from that state and then finally the value of the moves that can be max 100.
	memoryArr = {}
	
	# here is how a game board usually looks like:
		# 	self.__board: np.ndarray[tuple[int, int], np.dtype[np.int8]] = np.array([
		# 	[-1, 0, -1, 0, -1, 0],
		# 	[0, -1, 0, -1, 0, -1],
		# 	[0, 0, 0, 0, 0, 0],
		# 	[0, 0, 0, 0, 0, 0],
		# 	[1, 0, 1, 0, 1, 0],
		# 	[0, 1, 0, 1, 0, 1]
		# ], dtype=np.int8).reshape(self.SIZE, self.SIZE).T
	
	def __init__(self,startFresh:bool):
		super().__init__()
		if startFresh:
			# since we are doing a fresh start, we will create a new memory array full of all possible states and moves and give them a value of 100.
			# we get a new Board object to get the possible states and moves.
			# we always assume for this board that the player is positive and the enemy is negative.
			board = Board()
			for x in range(board.SIZE):
				for y in range(board.SIZE):
					pos = (x, y)
					if _s(board[pos]) == 1:
						possible_ends = board.get_correct_moves(pos)
						for end in possible_ends:
							self.memoryArr[(board,pos,end)] = 100
		else:
			# we will load the memory array from the file.
			self.loadTraining()
		


	def decide_move(self, board: iplayer.Board, sign: int) -> tuple[tuple[int, int], tuple[int, int]]:
		# we use dynamic programming to find the best move:
		# we will have an  array of all possible moves and their values starting from 100 for each state in the game.
		# every time an enemy is given, we will play against the enemy and then if the game ends in a loss we remove -1 from all the moves that led to that loss.
		possible_starts = []
		for x in range(board.SIZE):
			for y in range(board.SIZE):
				pos = (x, y)
				if _s(board[pos]) == sign:
					possible_starts.append(pos)
		
		assert possible_starts

		possible_values = {}
		# we pick the start by checking all of them in our memory and picking them ranndomly with involved probability from the memory array.
		for start in possible_starts:
			possible_ends = board.get_correct_moves(start)
			if not possible_ends:
				continue
			for end in possible_ends:# appending start,end and the value of the move to the possible values array:
				if (board,start,end) in self.memoryArr:
					possible_values[start,end] = self.memoryArr[(board,start,end)]
				else:
					possible_values[start,end] = 100

		# we will get the move with the highest value.
		maxValue = -1
		maxValueLocations = {}
		
		# Iterate through all key-value pairs
		for (start, end), value in possible_values.items():
			if value > maxValue:
				maxValue = value
				maxValueLocations = {(start, end)}
			elif value == maxValue:
				maxValueLocations.add((start, end))
				
		# if the amount of locations is more than one, we will pick one randomly depending on the probability of the move.
		if len(maxValueLocations) > 1:
			# Calculate the sum of the values
			sumValues = sum(possible_values[start, end] for start, end in maxValueLocations)
			# Calculate the probability of each move
			probabilities = {move: possible_values[move] / sumValues for move in maxValueLocations}
			# Pick a random move
			move = random.choices(list(probabilities.keys()), list(probabilities.values()))[0]
			return move
		else:
			# If there is only one move, return it
			return list(maxValueLocations)[0]

		
		raise ValueError("Tried to ask for a move when there are no possible moves")

	def do_training_step(self, enemy: iplayer.IPlayer):
		# this is pretty much the same as decide_move but we will also update the memory array if we lose or win.
		# we will get the best move from the memory array and then play it.
		
		# creating initial board to start the game:
		board = Board()
		# we assume the enemy starts first.
		# we will play the game until it ends while saving all the moves we make in:
		movesMade = {}
		# this will hold the board,start,end and with it at the end we will update the memory array by incrementing all the moves that led to a win by 1 and decrementing all the moves that led to a loss by 1.
		
		# we will play the game until it ends:
		while True:
			# we will get the move from the enemy:
			start,end = enemy.decide_move(board,-1)
			# we will make the move:
			board.make_move(start,end)
			# we will check if the game is over:
			if board.game_state != None:
				if board.game_state == 1:
					# we will update the memory array by incrementing all the moves that led to a win by 1 and decrementing all the moves that led to a loss by 1.
					for move in movesMade:
						if movesMade[move]:
							self.memoryArr[move.keys()] += 1
						else:
							self.memoryArr[move.keys()] -= 1
				break
			# we will get the move from the agent:
			start,end = self.decide_move(board,1)
			# we will make the move:
			board.make_move(start,end)
			# we will save the move:
			movesMade[board,start,end] = 1
			# we will check if the game is over:
			if board.game_state != None:
				if board.game_state == 1:
					# we will update the memory array by incrementing all the moves that led to a win by 1 and decrementing all the moves that led to a loss by 1.
					for move in movesMade:
						if movesMade[move]:
							self.memoryArr[move.keys()] += 1
						else:
							self.memoryArr[move.keys()] -= 1
				break
		# we will save the memory array to a file:
		self.saveTraining()
		
			

	
	def saveTraining(self, path: str) -> None:
		path = path or "dynamic_learning_agent"
		with open(path+".dynamicProgrammingSave", "wb") as f:
			pickle.dump(self, f)
			
	def loadTraining(self, path: str) -> bool:
		path = path or "dynamic_learning_agent"
		try:
			with open(path+".dynamicProgrammingSave", "rb") as f:
				self = pickle.load(f)
			return True
		except FileNotFoundError:
			return False
	
	def __str__(self) -> str:
		return "Dynamic Learning Agent"