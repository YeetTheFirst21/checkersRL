# Src: https://github.com/pyimgui/pyimgui/blob/master/doc/examples/plots.py

import glfw
import OpenGL.GL as gl
import imgui
from imgui.integrations.glfw import GlfwRenderer
from PIL import Image
import numpy as np

import sys
import pathlib
from typing import Optional
from time import sleep
import json
from collections.abc import Callable
from dataclasses import dataclass

import algo.board
from algo.board import Board
import algo.iplayer as iplayer


CUR_DIR = pathlib.Path(__file__).parent.resolve().absolute()


class ImageTexture:
	def __load_image(self, path: pathlib.Path, filter: Callable[[Image.Image], Image.Image] = lambda x: x) -> Optional[None]:
		try:
			with Image.open(path) as _image:
				image = _image.convert("RGBA")
			image = filter(image)
			img_data = image.tobytes()
			width, height = image.size

			texture_id = gl.glGenTextures(1)
			gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
			gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img_data)
			gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
			gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
			gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

			return texture_id

		except Exception as e:
			print(f"Failed to load texture {path}: {e}")
			return None

	def __init__(self, path: str) -> None:
		full_path = (CUR_DIR / path).resolve().absolute()

		def enabled_filter(image: Image.Image) -> Image.Image:
			with_outline = Image.new("RGBA", image.size, (0, 0, 0, 0))
			with_outline.paste(
				Image.new("RGBA", image.size, (255, 244, 161, 255)),
				mask=image
			)

			scale_factor = 1.1
			with_outline = with_outline.resize(
				(int(image.width * scale_factor), int(image.height * scale_factor)),
				Image.Resampling.BICUBIC
			)

			with_outline.paste(
				image,
				(
					(with_outline.width - image.width) // 2,
					(with_outline.height - image.height) // 2
				),
				image
			)
			return with_outline
		
		self.enabled_texture_id: Optional[int] = self.__load_image(
			full_path, enabled_filter)

		self.disabled_texture_id: Optional[int] = self.__load_image(full_path)

	@staticmethod
	def __remove_texture(texture_id: Optional[int]) -> None:
		if texture_id is not None and gl.glIsTexture(texture_id):
			# https://stackoverflow.com/a/60352108/8302811
			c_id = (gl.GLuint * 1) (texture_id)
			gl.glDeleteTextures(1, c_id)

	def __del__(self) -> None:
		self.__remove_texture(self.enabled_texture_id)
		self.__remove_texture(self.disabled_texture_id)

class UIState:
	def __init__(self) -> None:
		self.show_settings: bool = True
		self.textures: dict[int, ImageTexture] = {
			-2: ImageTexture("./icons/negative_king.png"),
			-1: ImageTexture("./icons/negative_simple.png"),
			0: ImageTexture("./icons/empty.png"),
			1: ImageTexture("./icons/positive_simple.png"),
			2: ImageTexture("./icons/positive_king.png"),
		}

		self.selected_pos: Optional[tuple[
			tuple[int, int],
			set[tuple[int, int]]
		]] = None

		self.positive_player_i = 0
		self.negative_player_i = 0
		user_input = iplayer.UserInput()
		self.players: list[iplayer.IPlayer] = [
			user_input
		]
		self.board: Board
		self.reset_board()

	def reset_board(self) -> None:
		self.board = Board()

	# Handlers
	def on_pressed_tile(self, pos: tuple[int, int]) -> None:
		if self.selected_pos and pos in self.selected_pos[1]:
			self.board.make_move(self.selected_pos[0], pos)
			self.selected_pos = None
			return

		if not self.board.is_valid_pos(pos) or not self.board[pos] or \
				(self.selected_pos and pos == self.selected_pos[0]) or \
				algo.board._s(self.board[pos]) != self.board.turn_sign or \
				not self.board.get_correct_moves(pos):
			self.selected_pos = None
			return

		self.selected_pos = (
			pos,
			self.board.get_correct_moves(pos)
		)
		

def draw_board(state: UIState, pos: tuple[float, float], available_size: tuple[float, float], gap_portion: float = 0.07) -> None:
	used_size = min(available_size)
	d = 10
	size = (used_size - (state.board.SIZE + 1) * d) / (state.board.SIZE * (1 + gap_portion) + gap_portion)
	gap = size * gap_portion + d
	x_s = pos[0] + gap
	x_c = x_s
	y_c = pos[1] + gap

	for y in range(6):
		for x in range(6):
			pos = (x, y)
			piece = state.board[pos]
			sign = algo.board._s(piece)
			imgui.set_cursor_pos_x(x_c)
			imgui.set_cursor_pos_y(y_c)

			# Highlighting valid moves with nice green
			if state.selected_pos and pos in state.selected_pos[1]:
				imgui.push_style_color(imgui.COLOR_BUTTON, 0.0, 0.5, 0.0, 1.0)
				imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.0, 0.5, 0.0, 0.6)
				imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.0, 0.5, 0.0, 1.0)
			
			# Highlighting selected piece with nice yellow
			elif state.selected_pos and pos == state.selected_pos[0]:
				imgui.push_style_color(imgui.COLOR_BUTTON, 0.5, 0.5, 0.0, 1.0)
				imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.5, 0.5, 0.0, 0.6)
				imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.5, 0.5, 0.0, 1.0)
			
			# Dark tiles (which are valid)
			elif state.board.is_valid_pos(pos):
				imgui.push_style_color(imgui.COLOR_BUTTON, 0.55, 0.27, 0.07, 1.0)  # Dark brown
				imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.55, 0.27, 0.07, 0.6)
				imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.55, 0.27, 0.07, 1.0)

			# Light tiles
			else:
				imgui.push_style_color(imgui.COLOR_BUTTON, 0.87, 0.72, 0.53, 1.0)  # Light brown
				imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.87, 0.72, 0.53, 0.6)
				imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.87, 0.72, 0.53, 1.0)

			if piece == 0:
				imgui.image_button(state.textures[0].enabled_texture_id, size - 2, size)
			else:
				if state.board.get_correct_moves(pos) and sign == state.board.turn_sign:
					imgui.image_button(state.textures[piece].enabled_texture_id, size - 2, size)
				else:
					# imgui.push_style_var(imgui.STYLE_ALPHA, 0.5)
					# imgui.image_button(textures[piece].texture_id, size - 2, size)
					# imgui.pop_style_var(1)

					imgui.image_button(state.textures[piece].disabled_texture_id, size - 2, size)
			
			imgui.pop_style_color(3)

			if imgui.is_item_hovered():
				if imgui.is_mouse_clicked():
					state.on_pressed_tile(pos)

				with imgui.begin_tooltip():
					imgui.text(f"pos: {pos}")
					imgui.text(f"piece: {piece}")
					if state.selected_pos and state.selected_pos[0] != pos:
						imgui.text(f"Correct move: {state.board.is_move_correct(state.selected_pos[0], pos)}")

			x_c += size + gap

		y_c += size + gap
		x_c = x_s


def main():
	window = __impl_glfw_init()
	imgui.create_context()
	impl = GlfwRenderer(window)

	# INIT STAGE
	state = UIState()
	imgui.get_io().font_global_scale = 1.5

	# MAIN LOOP
	while not glfw.window_should_close(window):
		glfw.poll_events()
		impl.process_inputs()

		imgui.new_frame()

		turn_name = "positive" if state.board.turn_sign > 0 else "negative"

		# Board window
		# https://github.com/ocornut/imgui/issues/6872
		imgui.begin(f"Board - {turn_name} turn###Board", False, imgui.WINDOW_NO_COLLAPSE)
		imgui.set_window_size(500, 500)
		imgui.set_window_position(10, 50, imgui.ONCE)
		draw_board(
			state,
			imgui.get_cursor_pos(),
			imgui.get_content_region_available()
		)
		imgui.end()

		# Top menu bar
		with imgui.begin_main_menu_bar():
			clicked, _ = imgui.menu_item("Properties", "Ctrl+,", False)
			if clicked:
				state.show_settings = True

		# Settings window
		if state.show_settings:
			_, state.show_settings = imgui.begin("Properties", True, imgui.WINDOW_NO_COLLAPSE)
			imgui.set_window_size(400, 500)
			imgui.set_window_position(510, 50, imgui.APPEARING)

			if imgui.button("Reset board"):
				state.reset_board()

			_, state.board.enable_update_should_capture = imgui.checkbox(
				"Enable should capture rule", state.board.enable_update_should_capture)

			imgui.separator()
			imgui.text(f"{state.board.game_state}, turn: {turn_name}")

			# Players selection
			imgui.separator()
			with imgui.begin_table("Players selection", 2):
				player_names = [str(player) for player in state.players]

				imgui.table_next_row()
				imgui.table_next_column()
				imgui.text("Positive:")
				imgui.table_next_column()
				imgui.text("Negative:")

				imgui.table_next_row()
				imgui.table_next_column()
				imgui.set_next_item_width(-1)
				changed, new_val = imgui.combo(
					"##Positive player",
					state.positive_player_i,
					player_names
				)
				if changed:
					state.positive_player_i = new_val
				
				imgui.table_next_column()
				imgui.set_next_item_width(-1)
				changed, new_val = imgui.combo(
					"##Negative player",
					state.negative_player_i,
					player_names
				)
				if changed:
					state.negative_player_i = new_val
			
			imgui.separator()
			imgui.text(f"Board state:\n{state.board}")

			imgui.separator()
			imgui.text(f"Should capture:\npositive: {state.board.check_should_capture(1)}\nnegative: {state.board.check_should_capture(-1)}")

			imgui.separator()
			imgui.text("Correct moves cache:")
			imgui.text(json.dumps(
				{repr(k): v for (k,v) in state.board.get_correct_moves_cache().items()},
				indent=2
			))
			
			imgui.separator()
			changed, value = imgui.slider_float("Scale", imgui.get_io().font_global_scale, 0.3, 2.0)
			if changed:
				imgui.get_io().font_global_scale = value
			
			imgui.end()

		gl.glClearColor(0.0, 0.0, 0.0, 1)
		gl.glClear(gl.GL_COLOR_BUFFER_BIT)

		imgui.render()
		impl.render(imgui.get_draw_data())
		glfw.swap_buffers(window)
		sleep(10e-3)

	del state
	impl.shutdown()
	glfw.terminate()


def __impl_glfw_init():
	width, height = 1280, 720
	window_name = "CHECKERS LETS GOO"

	if not glfw.init():
		print("Could not initialize OpenGL context")
		sys.exit(1)

	# OS X supports only forward-compatible core profiles from 3.2
	glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
	glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
	glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

	glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

	# Create a windowed mode window and its OpenGL context
	window = glfw.create_window(int(width), int(height), window_name, None, None)
	glfw.make_context_current(window)

	if not window:
		glfw.terminate()
		print("Could not initialize Window")
		sys.exit(1)

	return window


if __name__ == "__main__":
	main()