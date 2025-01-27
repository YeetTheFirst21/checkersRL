import imgui

import pickle
import pathlib
from typing import Optional

from algo.board import Board
from .ui_state import UIState
from .utils import ROOT_DIR

class TreeVis:
	def __init__(self, state: UIState) -> None:
		self.ui_state = state
		self.parent_tree: Optional[dict[int, set[int]]] = None
		self.__parent_tree_size = 0
		self.show_window = False

		self.__me_integer_input = "1461501724784805657539772557023077283449775784707"

		self.parents: list[Board] = [Board()]
		self.me: Optional[Board] = Board()
		self.__me_int: Optional[int] = int(self.me)
		self.children: list[Board] = [Board()]

	def __draw_board(self, board: Board, size: tuple[float, float], mouse_pos: Optional[tuple[float, float]]) -> None:
		tile_size = (size[0] / board.SIZE, size[1] / board.SIZE)
		draw_list = imgui.get_window_draw_list()
		cur_pos = imgui.get_cursor_pos()
		cur_screen_pos = imgui.get_cursor_screen_pos()
		for y in range(board.SIZE):
			for x in range(board.SIZE):
				pos = (x, y)
				draw_list.add_rect_filled(
					cur_screen_pos[0] + x * tile_size[0],
					cur_screen_pos[1] + y * tile_size[1],
					cur_screen_pos[0] + (x + 1) * tile_size[0],
					cur_screen_pos[1] + (y + 1) * tile_size[1],
					imgui.get_color_u32_rgba(0.55, 0.27, 0.07, 1.0)
					if self.ui_state.board.is_valid_pos(pos)
					else imgui.get_color_u32_rgba(0.87, 0.72, 0.53, 1.0)
				)

				imgui.set_cursor_pos_x(cur_pos[0] + x * tile_size[0])
				imgui.set_cursor_pos_y(cur_pos[1] + y * tile_size[1])
				imgui.image(
					self.ui_state.textures[board[pos]].disabled_texture_id,
					tile_size[0], tile_size[1]
				)
		
		if mouse_pos and cur_screen_pos[0] < mouse_pos[0] < cur_screen_pos[0] + size[0] and cur_screen_pos[1] < mouse_pos[1] < cur_screen_pos[1] + size[1]:
			self.select_me(board)

	def load_tree(self) -> None:
		with open(ROOT_DIR / "parent_tree.pickle", "rb") as f:
			self.parent_tree = pickle.load(f)
		
		assert self.parent_tree
		self.__parent_tree_size = len(self.parent_tree)
		self.select_me(Board())

	def unload_tree(self) -> None:
		del self.parent_tree
		self.parent_tree = None
		self.__parent_tree_size = 0
	
	def select_me(self, board: Board) -> None:
		self.me = board

		if not self.parent_tree:
			return

		board_int = int(board)
		self.__me_int = board_int

		if board_int in self.parent_tree:
			self.parents = [
				Board.from_num_repr(parent_int) for parent_int in 
					self.parent_tree[board_int]
			]

		self.children = [
			Board.from_num_repr(child_int) for child_int, child_parent_ints in 
				self.parent_tree.items() if board_int in child_parent_ints
		]

	def draw(self):
		if not self.show_window:
			return
		
		with imgui.begin("Tree visualization", True) as (_, is_open):
			imgui.set_window_size(800, 600)
			self.show_window = is_open

			if imgui.button("Load tree" if self.parent_tree is None else "Unload tree"):
				if self.parent_tree is None:
					self.load_tree()
				else:
					self.unload_tree()

			imgui.same_line()
			if imgui.button("Select me"):
				self.select_me(Board.from_num_repr(int(self.__me_integer_input)))
			
			imgui.same_line()
			_, self.__me_integer_input = imgui.input_text("Me", self.__me_integer_input)

			imgui.text(f"Number of states saved: {self.__parent_tree_size}")
			imgui.text(f"Current state: {self.__me_int}")
			
			w, h = imgui.get_content_region_available()
			max_board_height = h * .25
			vertical_spacing = h * .125

			cur_pos = imgui.get_cursor_pos()

			mouse_pos = imgui.get_mouse_pos() if \
				imgui.is_mouse_clicked(imgui.MOUSE_BUTTON_LEFT) else None

			if self.parents:
				parent_delta = w / len(self.parents)
				parent_size = min(parent_delta * 0.8, max_board_height)
				for i, parent in enumerate(self.parents):
					imgui.set_cursor_pos((
						cur_pos[0] + (i + 0.2) * parent_delta,
						cur_pos[1]
					))
					self.__draw_board(parent, (parent_size, parent_size), mouse_pos)

			if self.me:
				me_size = max_board_height
				imgui.set_cursor_pos((
					cur_pos[0] + w / 2 - me_size / 2,
					cur_pos[1] + max_board_height + vertical_spacing
				))
				if self.me:
					self.__draw_board(self.me, (me_size, me_size), mouse_pos)

			if self.children:
				child_delta = w / len(self.children)
				child_size = min(child_delta * 0.8, max_board_height)
				y = cur_pos[1] + (max_board_height + vertical_spacing) * 2
				for i, child in enumerate(self.children):
					imgui.set_cursor_pos((
						cur_pos[0] + (i + 0.2) * child_delta, y
					))
					self.__draw_board(child, (child_size, child_size), mouse_pos)
			