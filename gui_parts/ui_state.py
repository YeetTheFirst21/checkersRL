import threading
from typing import Optional
from time import sleep
from math import exp
import glob

from .utils import ImageTexture, ROOT_DIR
from algo.board import Board, GameState, _s
from algo import iplayer
import algo.dynamicProgramming as dp
import algo.q_learning as ql
import algo.ddq_learning as ddqn

class UIState:
	def __init__(self) -> None:
		self.show_settings: bool = True
		self.show_test_window: bool = False
		self.textures: dict[int, ImageTexture] = {
			-2: ImageTexture("./icons/negative_king.png"),
			-1: ImageTexture("./icons/negative_simple.png"),
			0: ImageTexture("./icons/empty.png"),
			1: ImageTexture("./icons/positive_simple.png"),
			2: ImageTexture("./icons/positive_king.png"),
		}
		self.popup_content: str = ""

		self.automatic_computer_step: bool = True

		self.selected_pos: Optional[tuple[
			tuple[int, int],
			set[tuple[int, int]]
		]] = None

		self.player_i: dict[int, int] = { 1: 0, -1: 6 }
		self.players: list[iplayer.IPlayer] = [
			iplayer.UserInput(),
			iplayer.RandomPlayer(),
			dp.dynamicPlayer(),
			ql.QLearning(str(ROOT_DIR / "models/#1 DQN 90_50_50_1 76.908%.pth")),
			ql.QLearning(str(ROOT_DIR / "models/#2 DQN 90_50_20_1 59.670%.pth"), [90, 50, 20, 1]),
			ql.QLearning(str(ROOT_DIR / "models/#3 DQN 90_50_50_1 77.732%.pth")),
			ql.QLearning(str(ROOT_DIR / "models/#4 DQN 90_50_50_1 t.g. #3 84.448%.pth")),
			ql.QLearning(str(ROOT_DIR / "models/#5 DQN 90_52_1 78.628%.pth"), [90, 52, 1]),
			ql.QLearning(str(ROOT_DIR / "models/dqn_y87_90_52_1.pth"), [90, 52, 1]),
			ql.QLearning(str(ROOT_DIR / "models/dqn_y89_90_52_1.pth"), [90, 52, 1]),
			ql.QLearning(str(ROOT_DIR / "models/dqn_y99_90_52_1.pth"), [90, 52, 1]),
			ddqn.QLearning(str(ROOT_DIR / "models/ddqn87 90 50 50 1 q_1 tuned on ddqn86.pth"), [90, 50, 50, 1]),
			ddqn.QLearning(str(ROOT_DIR / "models/ddqn86 90 50 50 1 q_2 tuned on ddqn86.pth"), [90, 50, 50, 1]),
			ddqn.QLearning(str(ROOT_DIR / "models/ddqn85 90 50 50 1 q_2 tuned on dqn86.pth based on ddqn87.pth"), [90, 50, 50, 1]),
		]

		self.worker_thread_event = threading.Event()
		self.worker_thread_is_running = True
		self.worker_thread_is_working = False
		self.worker_thread_delay = .7
		self.worker_thread = threading.Thread(
			target=self.worker_thread_function,
			daemon=True
		)
		self.worker_thread.start()

		self.board: Board
		self.number_of_moves: int
		self.reset_board()

	def reset_board(self) -> None:
		self.selected_pos = None
		self.board = Board()
		self.number_of_moves = 0

	def get_player(self, sign: int) -> iplayer.IPlayer:
		return self.players[self.player_i[sign]]

	def get_player_list_name(self, index: int) -> str:
		return f"{self.players[index]}"

	@property
	def game_is_going(self) -> bool:
		return self.board.game_state == GameState.NOT_OVER

	@property
	def waiting_user_input(self) -> bool:
		return self.game_is_going and \
			isinstance(self.get_player(self.board.turn_sign), iplayer.UserInput)
	
	@property
	def can_do_computer_step(self) -> bool:
		return self.game_is_going and \
			not isinstance(self.get_player(self.board.turn_sign), iplayer.UserInput)

	# Handlers
	def on_pressed_tile(self, pos: tuple[int, int]) -> Optional[str]:
		if self.worker_thread_event.is_set():
			return "Computer is currently thinking..."

		if not self.waiting_user_input:
			return

		if self.selected_pos and pos in self.selected_pos[1]:
			self.board.make_move(self.selected_pos[0], pos)
			self.number_of_moves += 1
			self.selected_pos = None

			if self.automatic_computer_step and not self.waiting_user_input:
				self.worker_thread_event.set()

			return

		if not self.board.is_valid_pos(pos) or not self.board[pos] or \
				(self.selected_pos and pos == self.selected_pos[0]) or \
				_s(self.board[pos]) != self.board.turn_sign or \
				not next(self.board.get_correct_moves(pos), None):
			self.selected_pos = None
			return

		self.selected_pos = (
			pos,
			set(self.board.get_correct_moves(pos))
		)

	def worker_thread_function(self) -> None:
		while self.worker_thread_event.wait():
			self.worker_thread_event.clear()

			if not self.worker_thread_is_running:
				return

			self.selected_pos = None

			self.worker_thread_is_working = True
			while self.worker_thread_is_working and self.can_do_computer_step:
				start, end = self.get_player(self.board.turn_sign).decide_move(self.board)
				
				self.board.make_move(start, end)
				self.number_of_moves += 1

				if self.worker_thread_delay:
					sleep(1e-3 * (exp(self.worker_thread_delay) - 1))
			
			self.worker_thread_is_working = False
	
	def __del__(self) -> None:
		self.worker_thread_is_running = False
		self.worker_thread_pause_requested = True
		self.worker_thread_event.set()
		self.worker_thread.join()