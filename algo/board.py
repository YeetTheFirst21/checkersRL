import numpy as np

from dataclasses import dataclass
from typing import Optional

def _s(x: int) -> int:
	if x > 0:
		return 1
	elif x < 0:
		return -1
	return 0

@dataclass
class _c:
	x: int
	y: int

	def s(self) -> '_c':
		return _c(_s(self.x), _s(self.y))

	def __add__(self, other: '_c') -> '_c':
		return _c(self.x + other.x, self.y + other.y)
	
	def __sub__(self, other: '_c') -> '_c':
		return _c(self.x - other.x, self.y - other.y)
	
	def __getitem__(self, index: int) -> int:
		if index == 0:
			return self.x
		elif index == 1:
			return self.y
		raise IndexError("Invalid index")

class Board():
	SIZE = 6
	__directions = [
		_c(-1, -1),
		_c(1, -1),
		_c(1, 1),
		_c(-1, 1)
	]
	__invalid_board = np.array(
		[[False] * SIZE] * SIZE,
		dtype=np.bool
	).reshape(SIZE, SIZE)
	
	def __init__(self) -> None:
		self.__board: np.ndarray[tuple[int, int], np.dtype[np.int8]] = np.array([
			[-1, 0, -1, 0, -1, 0],
			[0, -1, 0, -1, 0, -1],
			[0, 0, 0, 0, 0, 0],
			[0, 0, 0, 0, 0, 0],
			[1, 0, 1, 0, 1, 0],
			[0, 1, 0, 1, 0, 1]
		], dtype=np.int8).reshape(self.SIZE, self.SIZE).T

		self.__positive_should_capture = False
		self.__negative_should_capture = False
		self.__enable_update_should_capture = True

	def check_should_capture(self, sign: int) -> bool:
		if sign > 0:
			return self.__positive_should_capture
		else:
			return self.__negative_should_capture

	def __invalid(self, pos: _c) -> bool:
		return pos.x not in range(self.SIZE) or pos.y not in range(self.SIZE)
	
	def __empty(self, pos: _c) -> bool:
		return self[pos] == 0
	
	def __enemy(self, pos1: _c, pos2: _c) -> bool:
		return np.sign(self[pos1]) == -np.sign(self[pos2])

	def __can_simple_capture(self, pos: _c, direction: _c) -> bool:
		enemy_pos = pos + direction
		empty_pos = enemy_pos + direction
		if self.__invalid(empty_pos):
			return False
		if not self.__empty(empty_pos) or not self.__enemy(pos, enemy_pos):
			return False
		return True
	
	def __can_king_capture(self, pos: _c, direction: _c) -> bool:
		next_next_pos = pos + direction
		while True:
			next_pos = next_next_pos
			next_next_pos = next_pos + direction
			if self.__invalid(next_next_pos):
				return False
			if self.__empty(next_next_pos) and self.__enemy(pos, next_pos):
				return True
	
	def __get_simple_directions(self, sign: int) -> list[_c]:
		if sign > 0:
			return self.__directions[:2]
		else:
			return self.__directions[2:]
	
	def __update_should_capture(self) -> None:
		# Determine if a player should capture
		should_capture = {-1: False, 1: False}
		for sign in [-1, 1]:
			simple_directions = self.__get_simple_directions(sign)

			for y in range(6):
				if should_capture[sign]:
					break

				for x in range(6):
					pos = _c(x, y)
					piece = self[pos]
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

	
	def is_move_correct(self, start: tuple[int, int], end: tuple[int, int]) -> bool:
		s = _c(*start)
		e = _c(*end)
		if self.__invalid(s) or self.__empty(s) or self.__invalid(e) or not self.__empty(e):
			return False
		
		# Diagonality check
		delta = e - s
		if abs(delta[0]) != abs(delta[1]):
			return False
		
		direction = delta.s()
		piece = self.__board[*s]
		t = abs(piece)
		sign = np.sign(piece)

		# Simple piece
		if t == 1:
			direction_index = self.__directions.index(direction)
			# Incorrect direction
			if direction_index < 2 != sign > 0:
				return False
			
			# Non-capture move
			next_pos = s + direction
			if next_pos == e:
				return self.check_should_capture(sign) # type: ignore
			
			# Capture move
			next_next_pos = next_pos + direction
			if next_next_pos == e and self.__enemy(s, next_pos):
				return True
			
			return False
		
		# King piece
		elif t == 2:
			cur_pos = s
			found_enemy = False
			while cur_pos != e:
				cur_pos += direction

				if self.__empty(cur_pos):
					continue

				if found_enemy or not self.__enemy(s, cur_pos):
					return False
				
				found_enemy = True
			
			return found_enemy == self.check_should_capture(sign) # type: ignore

		raise ValueError("Invalid piece on the board!")

	def get_correct_moves(self, start: tuple[int, int]) -> np.ndarray[tuple[int, int], np.dtype[np.bool]]:
		s = _c(*start)
		ret = self.__invalid_board.copy()
		if self.__invalid(s) or self.__empty(s):
			return ret
		
		piece = self.__board[*s]
		t = abs(piece)
		sign = np.sign(piece)

		# Simple piece
		if t == 1:
			for direction in self.__get_simple_directions(sign): # type: ignore
				next_pos = s + direction
				if self.__invalid(next_pos):
					continue

				# Simple move
				if self.__empty(next_pos):
					ret[*next_pos] = True
					continue

				# Capture move
				next_next_pos = next_pos + direction
				if not self.__enemy(s, next_pos) or self.__invalid(next_next_pos) or not self.__empty(next_next_pos):
					continue
				ret[*next_next_pos] = True
			
			return ret
		
		# King piece
		elif t == 2:
			for direction in self.__directions:
				cur_pos = s
				found_enemy = False
				while True:
					cur_pos += direction
					if self.__invalid(cur_pos):
						break

					if self.__empty(cur_pos):
						ret[*cur_pos] = True
						continue
					
					if self.__enemy(s, cur_pos):
						if found_enemy:
							break
						found_enemy = True
						continue
			
			return ret

		raise ValueError("Invalid piece on the board!")
	
	def make_move(self, start: tuple[int, int], end: tuple[int, int]) -> None:
		"""
		**Warning**: No checks are performed!

		Would update the board state, check if the piece should be promoted or capture again
		"""
		self.__board[end] = self.__board[start]
		self.__board[start] = 0

		# Check if the piece should be promoted
		if end[1] == 0 and self.__board[end] == 1:
			self.__board[end] = 2
		elif end[1] == self.SIZE - 1 and self.__board[end] == -1:
			self.__board[end] = -2
		
		# Check if the piece should capture again
		if self.__enable_update_should_capture:
			self.__update_should_capture()

	def is_game_over(self, turn_sign: int) -> Optional[int]:
		"""
		Returns:
			1 if positive player wins, -1 if negative player wins, 0 if the game is not over
		"""
		turns_pieces = []
		not_turn_has_pieces = False
		for x in range(6):
			for y in range(6):
				sign = np.sign(self.__board[x, y])
				if sign == turn_sign:
					turns_pieces.append(np.array([x, y]))
				elif sign != 0:
					not_turn_has_pieces = True
		
		if not turns_pieces:
			return -turn_sign
		elif not not_turn_has_pieces:
			return turn_sign
		
		for pos in turns_pieces[sign]:
			if any(self.get_correct_moves(pos)):
				return None
		return -turn_sign

	def __getitem__(self, pos: _c | tuple[int, int]) -> int:
		return self.__board[pos[0], pos[1]]

	def get_board(self) -> np.ndarray[tuple[int, int], np.dtype[np.int8]]:
		return self.__board.copy()

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