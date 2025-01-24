# https://github.com/pyimgui/pyimgui/blob/master/doc/examples/plots.py

import sys
import pathlib
from typing import Optional
from time import sleep
import json

import glfw
import OpenGL.GL as gl
import imgui
from imgui.integrations.glfw import GlfwRenderer
from PIL import Image
import numpy as np

from algo.board import Board


CUR_DIR = pathlib.Path(__file__).parent.resolve().absolute()


class ImageTexture:
	def __init__(self, path: str) -> None:
		self.texture_id: Optional[int]

		full_path = (CUR_DIR / path).resolve().absolute()

		try:
			image = Image.open(full_path)
			img_data = image.convert("RGBA").tobytes()
			width, height = image.size

			texture_id = gl.glGenTextures(1)
			gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
			gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img_data)
			gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
			gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
			gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

			self.texture_id = texture_id

		except Exception as e:
			self.texture_id = None
			print(f"Failed to load texture {full_path}: {e}")

	def __del__(self) -> None:
		if self.texture_id is not None and gl.glIsTexture(self.texture_id):
			# https://stackoverflow.com/a/60352108/8302811
			c_id = (gl.GLuint * 1) (self.texture_id)
			gl.glDeleteTextures(1, c_id)

def on_pressed_tile(board: Board, pos: tuple[int, int]) -> None:
	global selected_pos

	if selected_pos and selected_pos[1][pos]:
		_move_result = board.user_move(selected_pos[0], pos)
		selected_pos = None
		return

	if not board.is_valid_pos(pos) or not board[pos] or \
			(selected_pos and pos == selected_pos[0]):
		selected_pos = None
		return

	selected_pos = (
		pos,
		board.compute_correct_moves(pos)
	)
		

def draw_board(board: Board, pos: tuple[float, float], available_size: tuple[float, float], gap_portion: float = 0.07) -> None:
	used_size = min(available_size)
	d = 10
	size = (used_size - (board.SIZE + 1) * d) / (board.SIZE * (1 + gap_portion) + gap_portion)
	gap = size * gap_portion + d
	x_s = pos[0] + gap
	x_c = x_s
	y_c = pos[1] + gap

	for y in range(6):
		for x in range(6):
			pos = (x, y)
			piece = board[pos]
			imgui.set_cursor_pos_x(x_c)
			imgui.set_cursor_pos_y(y_c)

			# Highlighting valid moves with nice green
			if selected_pos and selected_pos[1][pos]:
				imgui.push_style_color(imgui.COLOR_BUTTON, 0.0, 0.5, 0.0, 1.0)
				imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.0, 0.5, 0.0, 0.6)
				imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.0, 0.5, 0.0, 1.0)
			
			# Highlighting selected piece with nice yellow
			elif selected_pos and pos == selected_pos[0]:
				imgui.push_style_color(imgui.COLOR_BUTTON, 0.5, 0.5, 0.0, 1.0)
				imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.5, 0.5, 0.0, 0.6)
				imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.5, 0.5, 0.0, 1.0)
			
			# Dark tiles (which are valid)
			elif board.is_valid_pos(pos):
				imgui.push_style_color(imgui.COLOR_BUTTON, 0.55, 0.27, 0.07, 1.0)  # Dark brown
				imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.55, 0.27, 0.07, 0.6)
				imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.55, 0.27, 0.07, 1.0)

			# Light tiles
			else:
				imgui.push_style_color(imgui.COLOR_BUTTON, 0.87, 0.72, 0.53, 1.0)  # Light brown
				imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.87, 0.72, 0.53, 0.6)
				imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.87, 0.72, 0.53, 1.0)
			
			if piece != 0:
				imgui.image_button(textures[piece].texture_id, size - 2, size)
			else:
				imgui.internal.push_item_flag(imgui.internal.ITEM_DISABLED, True)
				imgui.image_button(textures[0].texture_id, size - 2, size)
				imgui.internal.pop_item_flag()
			
			imgui.pop_style_color(3)

			if imgui.is_item_hovered():
				if imgui.is_mouse_clicked():
					on_pressed_tile(board, pos)

				with imgui.begin_tooltip():
					imgui.text(f"pos: {pos}")
					imgui.text(f"piece: {piece}")
					if selected_pos and selected_pos[0] != pos:
						imgui.text(f"Correct move: {board.is_move_correct(selected_pos[0], pos)}")

			x_c += size + gap

		y_c += size + gap
		x_c = x_s


selected_pos: Optional[tuple[
	tuple[int, int],
	np.ndarray
]]

def main():
	window = __impl_glfw_init()
	imgui.create_context()
	impl = GlfwRenderer(window)

	# INIT STAGE
	show_settings = True
	imgui.get_io().font_global_scale = 1.5

	global textures
	textures = {
		-2: ImageTexture("./icons/negative_king.png"),
		-1: ImageTexture("./icons/negative_simple.png"),
		0: ImageTexture("./icons/empty.png"),
		1: ImageTexture("./icons/positive_simple.png"),
		2: ImageTexture("./icons/positive_king.png"),
	}

	global selected_pos
	selected_pos = None

	board = Board()

	# MAIN LOOP
	while not glfw.window_should_close(window):
		glfw.poll_events()
		impl.process_inputs()

		imgui.new_frame()

		# Board window
		imgui.begin("Board", False, imgui.WINDOW_NO_COLLAPSE)
		imgui.set_window_size(500, 500)
		imgui.set_window_position(10, 50, imgui.ONCE)
		draw_board(
			board,
			imgui.get_cursor_pos(),
			imgui.get_content_region_available()
		)
		imgui.end()

		# Top menu bar
		with imgui.begin_main_menu_bar():
			clicked, _ = imgui.menu_item("Properties", "Ctrl+,", False)
			if clicked:
				show_settings = True

		# Settings window
		if show_settings:
			_, show_settings = imgui.begin("Properties", True, imgui.WINDOW_NO_COLLAPSE)
			imgui.set_window_size(400, 500)
			imgui.set_window_position(510, 50, imgui.APPEARING)

			if imgui.button("Reset board"):
				board = Board()

			_, board.enable_update_should_capture = imgui.checkbox(
				"Enable should capture rule", board.enable_update_should_capture)
			
			imgui.separator()
			imgui.text(f"Board state:\n{board}")

			imgui.separator()
			imgui.text(f"Should capture:\npositive: {board.check_should_capture(1)}\nnegative: {board.check_should_capture(-1)}")

			imgui.separator()
			imgui.text(f"Game state: {board.game_state}")

			imgui.separator()
			imgui.text("Correct moves cache:")
			imgui.text(json.dumps(
				{repr(k): v for (k,v) in board.get_correct_moves_cache().items()},
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