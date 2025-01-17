import numpy as np

import math
from typing import Optional
from abc import ABC, abstractmethod


class Player(ABC):
	pass

class Board():
	SIZE = 6
	__directions = np.array([
		[-1, -1],
		[1, -1],
		[1, 1],
		[-1, 1]
	])

	@classmethod
	def __direction_index(cls, direction: np.ndarray) -> int:
		for i, d in enumerate(cls.__directions):
			if d == direction:
				return i
		raise ValueError("Invalid direction")

	def __init__(self, positive_player: Player, negative_player: Player) -> None:
		self.__positive_player = positive_player
		self.__negative_player = negative_player

		self.__board = np.array([
			[-1, 0, -1, 0, -1, 0],
			[0, -1, 0, -1, 0, -1],
			[0, 0, 0, 0, 0, 0],
			[0, 0, 0, 0, 0, 0],
			[1, 0, 1, 0, 1, 0],
			[0, 1, 0, 1, 0, 1]
		]).T

		self.__positive_should_capture = False
		self.__negative_should_capture = False

	def __check_should_capture(self, sign: int) -> bool:
		if sign > 0:
			return self.__positive_should_capture
		else:
			return self.__negative_should_capture

	def __invalid(self, pos: np.ndarray) -> bool:
		return pos[0] not in range(self.SIZE) or pos[1] not in range(self.SIZE)
	
	def __empty(self, pos: np.ndarray) -> bool:
		return self.__board[*pos] == 0
	
	def __enemy(self, pos1: np.ndarray, pos2: np.ndarray) -> bool:
		return np.sign(self.__board[*pos1]) == -np.sign(self.__board[*pos2])

	def __can_simple_capture(self, pos: np.ndarray, direction: np.ndarray) -> bool:
		enemy_pos = pos + direction
		empty_pos = enemy_pos + direction
		if self.__invalid(empty_pos):
			return False
		if not self.__empty(empty_pos) or not self.__enemy(pos, enemy_pos):
			return False
		return True
	
	def __can_king_capture(self, pos: np.ndarray, direction: np.ndarray) -> bool:
		next_next_pos = pos + direction
		while True:
			next_pos = next_next_pos
			next_next_pos = next_pos + direction
			if self.__invalid(next_next_pos):
				return False
			if self.__empty(next_next_pos) and self.__enemy(pos, next_pos):
				return True
	
	def __on_board_update(self) -> None:
		# Determine if a player should capture
		should_capture = {-1: False, 1: False}
		for sign in [-1, 1]:
			if sign > 0:
				simple_directions = self.__directions[:2]
			else:
				simple_directions = self.__directions[2:]

			for y in range(6):
				if should_capture[sign]:
					break

				for x in range(6):
					pos = np.array([x, y])
					piece = self.__board[*pos]
					if np.sign(piece) != sign:
						continue
					t = abs(piece)
					if t == 1:
						for direction in simple_directions:
							if self.__can_simple_capture(pos, direction):
								should_capture[sign] = True
								break
					elif t == 2:
						for direction in self.__directions:
							if self.__can_king_capture(pos, direction):
								should_capture[sign] = True
								break

					if should_capture[sign]:
						break
		
		self.__positive_should_capture = should_capture[1]
		self.__negative_should_capture = should_capture[-1]

	
	def is_move_correct(self, start: np.ndarray, end: np.ndarray) -> bool:
		if self.__invalid(start) or self.__invalid(end) or not self.__empty(end):
			return False
		
		piece = self.__board[*start]
		if piece == 0:
			return False
		
		# Diagonality check
		delta = end - start
		if abs(delta[0]) != abs(delta[1]):
			return False
		
		direction = np.sign(delta)
		t = abs(piece)
		sign = np.sign(piece)

		# Simple piece
		if t == 1:
			direction_index = self.__direction_index(direction)
			# Incorrect direction
			if direction_index < 2 != sign > 0:
				return False
			
			# Non-capture move
			next_pos = start + direction
			if next_pos == end:
				return self.__check_should_capture(sign) # type: ignore
			
			# Capture move
			next_next_pos = next_pos + direction
			if next_next_pos == end and self.__enemy(start, next_pos):
				return True
			
			return False
		
		# King piece
		elif t == 2:
			cur_pos = start
			found_enemy = False
			while cur_pos != end:
				cur_pos += direction

				if self.__empty(cur_pos):
					continue

				if found_enemy or not self.__enemy(start, cur_pos):
					return False
				
				found_enemy = True
			
			return found_enemy == self.__check_should_capture(sign) # type: ignore

		
		raise ValueError("Invalid piece on the board!")

	
	def __str__(self) -> str:
		ret = ""
		for row in self.__board:
			for square in row:
				if square == 1:
					piece = "|p"
				elif square == -1:
					piece = "|n"
				elif square == 2:
					piece = "|P"
				elif square == -2:
					piece = "|N"
				else:
					piece = "| "
				ret += piece
			ret += "|\n"
		return ret