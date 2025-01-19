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
	
	def __eq__(self, value: '_c') -> bool:
		return self.x == value.x and self.y == value.y
	
	def __getitem__(self, index: int) -> int:
		if index == 0:
			return self.x
		elif index == 1:
			return self.y
		raise IndexError("Invalid index")
	
	def __hash__(self) -> int:
		# https://stackoverflow.com/a/4005376/8302811
		return hash((self.x, self.y))
	
	def __repr__(self) -> str:
		return f"({self.x}, {self.y})"

class Board():
	SIZE = 6
	TILING_PARITY = 0
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

		self.__correct_moves_cache: dict[tuple[_c, _c], bool] = {}
		self.__game_state_cache: dict[int, Optional[int]] = {}

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
		return _s(self[pos1]) == -_s(self[pos2])
	
	def __get_simple_directions(self, sign: int) -> list[_c]:
		if sign > 0:
			return self.__directions[:2]
		else:
			return self.__directions[2:]
	
	def __update_should_capture(self) -> None:
		# Determine if a player should capture
		should_capture = {-1: False, 1: False}
		# We are iterating over signs first, so that we can break preliminary
		for sign in [-1, 1]:
			simple_directions = self.__get_simple_directions(sign)

			for y in range(6):
				if should_capture[sign]:
					break

				for x in range(6):
					pos = _c(x, y)
					piece = self[pos]
					if _s(piece) != sign:
						continue
					t = abs(piece)

					# Simple piece
					if t == 1:
						for direction in simple_directions:
							enemy_pos = pos + direction
							empty_pos = enemy_pos + direction
							if not (
								self.__invalid(empty_pos) or \
								not self.__empty(empty_pos) or \
								not self.__enemy(pos, enemy_pos)
							):
								should_capture[sign] = True
								break
					
					# King piece
					elif t == 2:
						for direction in self.__directions:
							can_king_capture = False
							next_next_pos = pos + direction
							# We will iterate here until we reach the enemy and empty spot afterward
							while True:
								next_pos = next_next_pos
								next_next_pos = next_pos + direction

								# We are out of the board
								if self.__invalid(next_next_pos):
									break

								# The fact that we are here means that we haven't met anyone yet, so just continue
								if self.__empty(next_pos):
									continue

								# The fact that we are here means that next_pos is not empty
								# So next_next_pos should be empty and the next_pos should be an enemy
								can_king_capture = self.__empty(next_next_pos) and self.__enemy(pos, next_pos)
								break

							if can_king_capture:
								should_capture[sign] = True
								break

					if should_capture[sign]:
						break
		
		self.__positive_should_capture = should_capture[1]
		self.__negative_should_capture = should_capture[-1]

	
	def is_move_correct(self, start: tuple[int, int], end: tuple[int, int]) -> bool:
		args = (_c(*start), _c(*end))
		if args in self.__correct_moves_cache:
			return self.__correct_moves_cache[args]
		
		ret = self.__compute_correct_move(*args)
		self.__correct_moves_cache[args] = ret
		return ret

	def __compute_correct_move(self, s: _c, e: _c) -> bool:
		if self.__invalid(s) or self.__empty(s) or self.__invalid(e) or not self.__empty(e):
			return False
		
		# Diagonality check
		delta = e - s
		if abs(delta[0]) != abs(delta[1]):
			return False
		
		direction = delta.s()
		piece = self.__board[*s]
		t = abs(piece)
		sign = _s(piece)

		# Simple piece
		if t == 1:
			direction_index = self.__directions.index(direction)
			# Incorrect direction
			if (direction_index < 2) != (sign > 0):
				return False
			
			# Non-capture move
			next_pos = s + direction
			if next_pos == e:
				return not self.check_should_capture(sign)
			
			# Capture move
			next_next_pos = next_pos + direction
			if next_next_pos == e and self.__enemy(s, next_pos):
				return True
			
			return False
		
		# King piece
		elif t == 2:
			cur_pos = s
			found_enemy = False
			# We will iterate here until we reach the end position
			while cur_pos != e:
				cur_pos += direction

				if self.__empty(cur_pos):
					continue

				# The fact that we are here means that cur_pos is not empty
				# Found enemy for the second time on the path or jumping over our piece
				if found_enemy or not self.__enemy(s, cur_pos):
					return False
				
				found_enemy = True
			
			# We should find enemy if we should capture, and vise versa
			return found_enemy == self.check_should_capture(sign)

		raise ValueError("Invalid piece on the board!")

	def compute_correct_moves(self, start: tuple[int, int]) -> np.ndarray[tuple[int, int], np.dtype[np.bool]]:
		s = _c(*start)
		ret = self.__invalid_board.copy()
		if self.__invalid(s) or self.__empty(s):
			return ret
		
		piece = self.__board[*s]
		t = abs(piece)
		sign = _s(piece)

		# Simple piece
		if t == 1:
			for direction in self.__get_simple_directions(sign):
				next_pos = s + direction
				if self.__invalid(next_pos):
					continue

				if self.check_should_capture(sign):
					# Capture move
					next_next_pos = next_pos + direction
					if not self.__enemy(s, next_pos) or self.__invalid(next_next_pos) or not self.__empty(next_next_pos):
						continue
					ret[*next_next_pos] = True
				else:
					# Simple move
					if self.__empty(next_pos):
						ret[*next_pos] = True
						continue

			return ret
		
		# King piece
		elif t == 2:
			for direction in self.__directions:
				cur_pos = s
				found_enemy = False
				# We will iterate here until we reach the edge of the board
				while True:
					cur_pos += direction
					if self.__invalid(cur_pos):
						break

					if self.__empty(cur_pos):
						# We should find enemy if we should capture, and vise versa
						ret[*cur_pos] = found_enemy == self.check_should_capture(sign)
						continue

					# The fact that we are here means that cur_pos is not empty
					if not self.__enemy(s, cur_pos):
						# Jumping over our piece
						break
					else:
						if found_enemy:
							# Found enemy for the second time on the path
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

		# Invalidate the caches
		self.__correct_moves_cache.clear()
		self.__game_state_cache.clear()

		piece = self.__board[start]

		if (piece > 0 and self.__positive_should_capture) or \
			(piece < 0 and self.__negative_should_capture):
			# We should determine the enemy and capture
			e = _c(*end)
			s = _c(*start)
			direction = (e - s).s()
			next_pos = s
			enemy_pos: Optional[_c] = None
			while True:
				next_pos += direction
				if self.__invalid(next_pos):
					break
				if self.__enemy(s, next_pos):
					enemy_pos = next_pos
					break
			assert enemy_pos is not None # We should have found the enemy, cos we have to capture now
			self.__board[enemy_pos.x, enemy_pos.y] = 0

		# Move our piece
		self.__board[end] = piece
		self.__board[start] = 0

		# Check if the piece should be promoted
		if end[1] == 0 and self.__board[end] == 1:
			self.__board[end] = 2
		elif end[1] == self.SIZE - 1 and self.__board[end] == -1:
			self.__board[end] = -2
		
		# Check if the piece should capture again
		if self.__enable_update_should_capture:
			self.__update_should_capture()

	def get_game_state(self, turn_sign: int) -> Optional[int]:
		"""
		Returns:
			1 if positive player wins, -1 if negative player wins, None if the game is not over
		"""
		if turn_sign in self.__game_state_cache:
			return self.__game_state_cache[turn_sign]
		
		ret = self.__compute_game_state(turn_sign)
		self.__game_state_cache[turn_sign] = ret
		return ret

	def __compute_game_state(self, turn_sign: int) -> Optional[int]:
		"""
		1 if positive player wins, -1 if negative player wins, None if the game is not over
		"""
		turns_pieces: list[tuple[int, int]] = []
		opp_turn_has_pieces = False
		for x in range(6):
			for y in range(6):
				sign = _s(self.__board[x, y])
				if sign == turn_sign:
					turns_pieces.append((x, y))
				elif sign != 0:
					opp_turn_has_pieces = True
		
		if not turns_pieces:
			return -turn_sign
		elif not opp_turn_has_pieces:
			return turn_sign
		
		for pos in turns_pieces:
			if np.any(self.compute_correct_moves(pos)):
				return None
		return -turn_sign

	def __getitem__(self, pos: _c | tuple[int, int]) -> int:
		return self.__board[pos[0], pos[1]]

	def get_board(self) -> np.ndarray[tuple[int, int], np.dtype[np.int8]]:
		return self.__board.copy()

	def is_valid_pos(self, pos: tuple[int, int]) -> bool:
		return pos[0] in range(self.SIZE) and pos[1] in range(self.SIZE) and (pos[0] + pos[1]) % 2 == self.TILING_PARITY

	def __repr__(self) -> str:
		ret = ""
		for y in range(self.SIZE):
			for x in range(self.SIZE):
				ret += f"|{self[x, y]:2}"
			ret += "|\n"
		return ret
	

	# Debugging methods
	def get_correct_moves_cache(self) -> dict[tuple[_c, _c], bool]:
		return self.__correct_moves_cache