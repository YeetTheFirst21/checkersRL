import numpy as np

from typing import Optional
from dataclasses import dataclass
from enum import Enum

from .iplayer import *

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

	def tuple(self) -> tuple[int, int]:
		return (self.x, self.y)

class GameState(Enum):
	NOT_OVER = 0
	POSITIVE_WINS = 1
	NEGATIVE_WINS = -1

	def __str__(self) -> str:
		return self.name

class Board():
	SIZE = 6
	TILING_PARITY = 0
	__directions = [
		_c(-1, -1),
		_c(1, -1),
		_c(1, 1),
		_c(-1, 1)
	]
	
	def __init__(self, positive_player: IPlayer, negative_player: IPlayer) -> None:
		self.__board: np.ndarray[tuple[int, int], np.dtype[np.int8]] = np.array([
			[-1, 0, -1, 0, -1, 0],
			[0, -1, 0, -1, 0, -1],
			[0, 0, 0, 0, 0, 0],
			[0, 0, 0, 0, 0, 0],
			[1, 0, 1, 0, 1, 0],
			[0, 1, 0, 1, 0, 1]
		], dtype=np.int8).reshape(self.SIZE, self.SIZE).T

		self.__should_capture = {1: False, -1: False}
		self.__enable_update_should_capture = True

		self.__correct_moves_cache: dict[_c, dict[_c, bool]] = {}

		self.__turn_sign = 1
		self.__game_state_cache: Optional[GameState] = GameState.NOT_OVER
		self.players: dict[int, IPlayer] = {
			1: positive_player,
			-1: negative_player
		}

	def check_should_capture(self, sign: int) -> bool:
		return self.__should_capture[sign]

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
		self.__should_capture = {-1: False, 1: False}
		should_capture = self.__should_capture
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
		
		piece = self.__board[*s]
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

	def get_correct_moves(self, start: tuple[int, int]) -> set[tuple[int, int]]:
		s = _c(*start)
		if self.__invalid(s) or self.__empty(s):
			return set()
		
		piece = self.__board[*s]
		t = abs(piece)
		sign = _s(piece)

		if t != 1 and t != 2:
			return set()
		
		ret = set()
		for direction in (self.__get_simple_directions(sign) if t == 1 else self.__directions):
			e = s + direction

			# Moving a bit more forward, if there is an enemy
			if self.__invalid(e):
				continue
			if self.__enemy(s, e):
				e += direction
			
			if self.__is_move_correct(s, e):
				ret.add(e.tuple())
		
		return ret
	
	def __invalidate_cache(self) -> None:
		self.__correct_moves_cache.clear()
		self.__game_state_cache = None

	def __move_piece(self, start: tuple[int, int], end: tuple[int, int]) -> None:
		"""
		**Warning**: No checks are performed and no turn change is made!

		Would update the board state, check if the piece should be promoted or capture again
		"""

		self.__invalidate_cache()

		piece = self.__board[start]

		if self.check_should_capture(_s(piece)):
			# We should determine the enemy and capture
			s = _c(*start)
			enemy_pos = s + (_c(*end) - s).s()
			assert self.__enemy(s, enemy_pos)
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

	def user_move(self, start: tuple[int, int], end: tuple[int, int]) -> bool:
		"""
		**Warning**: It is not checked whether the move is correct or not.

		Would update the board state, check if it's user's turn and
		 	if the piece should be promoted or capture again
			
		Returns:
			True if the move was successful, False otherwise
		"""

		# Check if it's the user's turn
		if not isinstance(self.players[self.__turn_sign], UserInput) or \
				_s(self.__board[start]) != self.__turn_sign:
			return False
		
		had_to_capture = self.check_should_capture(self.__turn_sign)
		self.__move_piece(start, end)

		# Change the turn
		#    If we should and can capture with the same piece, we should not change the turn
		if had_to_capture and self.check_should_capture(self.__turn_sign) and \
				self.get_correct_moves(end):
			return True
		
		self.__turn_sign = -self.__turn_sign
		return True

	@property
	def game_state(self) -> GameState:
		"""
		Returns:
			1 if positive player wins, -1 if negative player wins, None if the game is not over
		"""
		if self.__game_state_cache:
			return self.__game_state_cache
		
		ret = self.__compute_game_state()
		self.__game_state_cache = ret
		return ret

	@property
	def turn_sign(self) -> int:
		return self.__turn_sign

	def __compute_game_state(self) -> GameState:
		"""
		1 if positive player wins, -1 if negative player wins, None if the game is not over
		"""
		turn_sign = self.__turn_sign
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
			return GameState(-turn_sign)
		elif not opp_turn_has_pieces:
			return GameState(turn_sign)
		
		for pos in turns_pieces:
			if self.get_correct_moves(pos):
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
	

	# Debugging methods
	def get_correct_moves_cache(self) -> dict[tuple[tuple[int, int], tuple[int, int]], bool]:
		return {
			(s.tuple(), e.tuple()): v
			for s in self.__correct_moves_cache
			for e, v in self.__correct_moves_cache[s].items()
		}