import torch
import numpy as np

from typing import Optional, Iterator
from dataclasses import dataclass
from enum import Enum
import itertools

def _s(x: int) -> int:
	return int(np.sign(x))

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

	def tuple(self) -> tuple[int, int]:
		return (self.x, self.y)

class GameState(Enum):
	NOT_OVER = 0
	POSITIVE_WINS = 1
	NEGATIVE_WINS = -1
	DRAW = -2

	def __str__(self) -> str:
		return self.name

class Board():
	SIZE = 6
	TILING_PARITY = 0
	DRAW_NON_CAPTURE_MOVES = 50
	__directions = [
		_c(-1, -1),
		_c(1, -1),
		_c(1, 1),
		_c(-1, 1)
	]
	
	def __init__(self) -> None:
		self.__board: np.ndarray[tuple[int, int], np.dtype[np.int8]] = np.array([
			[-1, 0, -1, 0, -1, 0],
			[0, -1, 0, -1, 0, -1],
			[0, 0, 0, 0, 0, 0],
			[0, 0, 0, 0, 0, 0],
			[1, 0, 1, 0, 1, 0],
			[0, 1, 0, 1, 0, 1]
		], dtype=np.int8).reshape(self.SIZE, self.SIZE).T

		# self.__board: np.ndarray[tuple[int, int], np.dtype[np.int8]] = np.array([
		# 	[-1, 0, -1, 0, -1, 0],
		# 	[0, 0, 0, 0, 0, 0],
		# 	[0, 0, 0, 0, 0, 0],
		# 	[0, -1, 0, -1, 0, 0],
		# 	[1, 0, 2, 0, 2, 0],
		# 	[0, 1, 0, 1, 0, 1]
		# ], dtype=np.int8).reshape(self.SIZE, self.SIZE).T

		self.__should_capture = {1: False, -1: False}
		self.__enable_update_should_capture = True
		self.__moves_since_last_capture = 0

		self.__correct_moves_cache: dict[_c, dict[_c, bool]] = {}
		self.__tensor_cache: dict[tuple[bool, bool], torch.Tensor] = {}

		self.__turn_sign = 1
		self.__game_state_cache: Optional[GameState] = GameState.NOT_OVER

	def check_should_capture(self, sign: int) -> bool:
		return self.__should_capture[sign]

	def __invalid(self, pos: _c) -> bool:
		return pos.x not in range(self.SIZE) or pos.y not in range(self.SIZE)
	
	def __empty(self, pos: _c) -> bool:
		return self[pos] == 0
	
	def __enemy(self, pos1: _c, pos2: _c) -> bool:
		return _s(self[pos1]) == -_s(self[pos2])
	
	@staticmethod
	def __faster_iteration_end(pos: _c, i: int) -> _c:
		return Board.__faster_iteration_start(pos, i + 1)
	
	@staticmethod
	def __faster_iteration_start(pos: _c, i: int) -> _c:
		if i % 3 == 0:
			pos.y += 1
			return _c(pos.y % 2, pos.y)
		else:
			return _c(pos.x + 2, pos.y)
	
	def __get_simple_directions(self, sign: int) -> list[_c]:
		if sign > 0:
			return self.__directions[:2]
		else:
			return self.__directions[2:]
	
	def __update_should_capture(self) -> None:
		# Determine if a player should capture
		self.__should_capture = {-1: False, 1: False}
		should_capture = self.__should_capture
		# We are iterating over signs first, so that we can break preliminary
		for sign in [-1, 1]:
			simple_directions = self.__get_simple_directions(sign)

			pos = _c(0, -1)
			for i in range(18):
				pos = self.__faster_iteration_start(pos, i)
				piece = self[pos]
				if _s(piece) != sign:
					continue
				t = abs(piece)

				# Simple piece
				for direction in (simple_directions if t == 1 else self.__directions):
					enemy_pos = pos + direction
					empty_pos = enemy_pos + direction
					if not (
						self.__invalid(empty_pos) or \
						not self.__empty(empty_pos) or \
						not self.__enemy(pos, enemy_pos)
					):
						should_capture[sign] = True
						break

				if should_capture[sign]:
					break

	def __compute_correct_move(self, s: _c, e: _c) -> bool:
		if self.__invalid(s) or self.__empty(s) or self.__invalid(e) or not self.__empty(e):
			return False
		
		piece = self[s]
		t = abs(piece)
		sign = _s(piece)

		# Piece check
		if t != 1 and t != 2:
			return False
		
		# Diagonality check
		delta = e - s
		if abs(delta[0]) != abs(delta[1]):
			return False
		
		direction = delta.s()

		# Simple piece
		direction_index = self.__directions.index(direction)
		# Incorrect direction, if it's a simple piece
		if t == 1 and (direction_index < 2) != (sign > 0):
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
	
	def __is_move_correct(self, s: _c, e: _c) -> bool:
		if s in self.__correct_moves_cache and e in self.__correct_moves_cache[s]:
			return self.__correct_moves_cache[s][e]
	
		ret = self.__compute_correct_move(s, e)
		if s not in self.__correct_moves_cache:
			self.__correct_moves_cache[s] = {e: ret}
		else:
			self.__correct_moves_cache[s][e] = ret
		return ret

	def is_move_correct(self, start: tuple[int, int], end: tuple[int, int]) -> bool:
		return self.__is_move_correct(_c(*start), _c(*end))

	def get_correct_moves(self, start: tuple[int, int]) -> Iterator[tuple[int, int]]:
		s = _c(*start)
		if self.__invalid(s) or self.__empty(s):
			return
		
		piece = self[s]
		t = abs(piece)
		sign = _s(piece)

		if t != 1 and t != 2:
			return
		
		for direction in (self.__get_simple_directions(sign) if t == 1 else self.__directions):
			e = s + direction

			# Moving a bit more forward, if there is an enemy
			if self.__invalid(e):
				continue
			if self.__enemy(s, e):
				e += direction
			
			if self.__is_move_correct(s, e):
				yield e.tuple()
	
	def __get_possible_pos(self, sign: int) -> Iterator[tuple[int, int]]:
		pos = _c(0, 0)
		for i in range(18):
			if _s(self[pos]) == sign:
				yield pos.tuple()
			pos = self.__faster_iteration_end(pos, i)
		
		return

	def get_possible_pos(self) -> Iterator[tuple[int, int]]:
		return self.__get_possible_pos(self.__turn_sign)

	def __invalidate_cache(self) -> None:
		self.__correct_moves_cache.clear()
		self.__game_state_cache = None
		self.__tensor_cache.clear()

	def make_move(self, start: tuple[int, int], end: tuple[int, int]) -> int:
		"""
		**Warning**: No checks are performed and no turn change is made!

		Would update the board state, check if the piece should be promoted or capture again

		Returns: sign of the player who captured a piece or 0 if no capture was made
		"""

		had_to_capture = self.check_should_capture(self.__turn_sign)
		
		self.__invalidate_cache()

		piece = self.__board[start]

		ret = 0

		if had_to_capture:
			# We should determine the enemy and capture
			s = _c(*start)
			enemy_pos = s + (_c(*end) - s).s()
			assert self.__enemy(s, enemy_pos)
			self.__board[enemy_pos.x, enemy_pos.y] = 0
			ret = self.turn_sign

			self.__moves_since_last_capture = 0
		else:
			self.__moves_since_last_capture += 1

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

		# Change the turn
		#    If we should and can capture with the same piece, we should not change the turn
		if had_to_capture and self.check_should_capture(self.__turn_sign) and \
				next(self.get_correct_moves(end), None):
			return ret
		
		# 	Otherwise, change the turn
		self.__turn_sign = -self.__turn_sign
		return ret

	@property
	def game_state(self) -> GameState:
		if self.__game_state_cache:
			return self.__game_state_cache
		
		ret = self.__compute_game_state()
		self.__game_state_cache = ret
		return ret

	@property
	def turn_sign(self) -> int:
		return self.__turn_sign
	
	@property
	def moves_since_last_capture(self) -> int:
		return self.__moves_since_last_capture

	def __compute_game_state(self) -> GameState:
		if self.__moves_since_last_capture >= self.DRAW_NON_CAPTURE_MOVES:
			return GameState.DRAW

		turn_sign = self.__turn_sign
		opp_turn_has_pieces = next(self.__get_possible_pos(-turn_sign), None)
		turns_pieces = self.__get_possible_pos(turn_sign)
		first_piece = next(turns_pieces, None)
		
		if not first_piece:
			return GameState(-turn_sign)
		elif not opp_turn_has_pieces:
			return GameState(turn_sign)
		
		for pos in itertools.chain([first_piece], turns_pieces):
			if next(self.get_correct_moves(pos), None):
				return GameState.NOT_OVER
		
		return GameState(-turn_sign)

	def __getitem__(self, pos: _c | tuple[int, int]) -> int:
		return self.__board[pos[0], pos[1]]

	@property
	def board(self) -> np.ndarray[tuple[int, int], np.dtype[np.int8]]:
		return self.__board.copy()

	def is_valid_pos(self, pos: tuple[int, int]) -> bool:
		return pos[0] in range(self.SIZE) and pos[1] in range(self.SIZE) and (pos[0] + pos[1]) % 2 == self.TILING_PARITY
	
	@property
	def enable_update_should_capture(self) -> bool:
		return self.__enable_update_should_capture
	
	@enable_update_should_capture.setter
	def enable_update_should_capture(self, value: bool) -> None:
		if value == self.__enable_update_should_capture:
			return
		
		self.__enable_update_should_capture = value
		self.__invalidate_cache()

		if value:
			self.__update_should_capture()
		elif not value:
			self.__should_capture = {1: False, -1: False}

	def __repr__(self) -> str:
		ret = ""
		for y in range(self.SIZE):
			for x in range(self.SIZE):
				ret += f"|{self[x, y]:2}"
			ret += "|\n"
		return ret

	def __bare_byte_repr(self) -> bytes:
		arr = [
			int(self.turn_sign == 1),
			self.__should_capture[-1],
			self.__should_capture[1]
		]
		pos = _c(0, 0)
		for i in range(18):
			arr.append(int(self[pos]) + 2)
			pos = self.__faster_iteration_end(pos, i)
		
		return bytes(arr)

	def __int__(self) -> int:
		return int.from_bytes(
			self.__bare_byte_repr(),
			byteorder="big"
		)

	def __bytes__(self) -> bytes:
		return bytes([
			self.__enable_update_should_capture,
			self.__moves_since_last_capture,
		]) + self.__bare_byte_repr()
	
	def __iter__(self) -> Iterator[tuple[tuple[int, int], int]]:
		"""
		Returns pair pos and piece
		"""
		pos = _c(0, 0)
		for i in range(18):
			yield pos.tuple(), self[pos]
			pos = self.__faster_iteration_end(pos, i)

	def to_tensor(self, device, flipped = False) -> torch.Tensor:
		cache_index = (flipped, False)
		if cache_index in self.__tensor_cache:
			return self.__tensor_cache[cache_index].clone()
		
		self.__tensor_cache[cache_index] = torch.zeros(90, dtype=torch.float32, device=device)

		board = self.__board
		if flipped:
			board = -board.T
		
		pos = _c(0, 0)
		for i in range(18):
			#       possition coding                   piece coding
			index = ((pos.x + self.SIZE * pos.y) // 2) * 5 + (board[pos.x, pos.y] + 2)
			self.__tensor_cache[cache_index][index] = 1
			pos = self.__faster_iteration_end(pos, i)
		return self.__tensor_cache[cache_index].clone()
	
	def to_tensor3d(self, device, flipped = False) -> torch.Tensor:
		cache_index = (flipped, False)
		if cache_index in self.__tensor_cache:
			return self.__tensor_cache[cache_index].clone()
		
		self.__tensor_cache[cache_index] = torch.zeros(3, 6, 5, dtype=torch.float32, device=device)

		board = self.__board
		if flipped:
			board = -board.T
		
		pos = _c(0, 0)
		for i in range(18):
			self.__tensor_cache[cache_index][pos.x // 2][pos.y][board[pos.x, pos.y] + 2] = 1
			pos = self.__faster_iteration_end(pos, i)
		return self.__tensor_cache[cache_index].clone()
	
	@classmethod
	def from_num_repr(cls, value: int | bytes) -> 'Board':
		ret = cls()

		# Int is reserved for the bare byte representation
		if isinstance(value, int):
			arr = value.to_bytes(21, "big")

		# Bytes is reserved for the full byte representation
		elif isinstance(value, bytes):
			ret.__enable_update_should_capture = bool(value[0])
			ret.__moves_since_last_capture = value[1]
			arr = value[2:]
		
		ret.__turn_sign = 1 if arr[0] else -1
		ret.__should_capture = {1: bool(arr[2]), -1: bool(arr[1])}

		pos = _c(0, 0)
		for i in range(18):
			ret.__board[pos.x, pos.y] = arr[i + 3] - 2
			pos = cls.__faster_iteration_end(pos, i)

		return ret

	# Debugging methods
	def get_correct_moves_cache(self) -> dict[tuple[tuple[int, int], tuple[int, int]], bool]:
		return {
			(s.tuple(), e.tuple()): v
			for s in self.__correct_moves_cache
			for e, v in self.__correct_moves_cache[s].items()
		}