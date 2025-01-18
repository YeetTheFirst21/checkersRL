# https://github.com/pyimgui/pyimgui/blob/master/doc/examples/plots.py

import os
import sys
import pathlib
from typing import Optional
from time import sleep

import glfw
import OpenGL.GL as gl
import imgui
from imgui.integrations.glfw import GlfwRenderer
from PIL import Image

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


def PressedButton(x, y):
	print(f"Button at ({x}, {y}) pressed")

def draw_board(board: Board, pos: tuple[float, float], available_size: tuple[float, float], gap_portion: float = 0.2) -> None:
	used_size = min(available_size)
	size = used_size / (board.SIZE * (1 + gap_portion) + gap_portion)
	gap = size * gap_portion
	delta = size + gap
	x_s = pos[0] + gap
	x_c = x_s
	y_c = pos[1] + gap

	for y in range(6):
		for x in range(6):
			piece = board[x, y]
			imgui.set_cursor_pos_x(x_c)
			imgui.set_cursor_pos_y(y_c)

			# Check if in diagonal to paint diagonals dark brown and rest light brown:
			if (x + y) % 2 == 0:
				imgui.push_style_color(imgui.COLOR_BUTTON, 0.87, 0.72, 0.53, 1.0)  # Light brown
				imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.87, 0.72, 0.53, 0.6)
				imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.87, 0.72, 0.53, 1.0)
			else:
				imgui.push_style_color(imgui.COLOR_BUTTON, 0.55, 0.27, 0.07, 1.0)  # Dark brown
				imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.55, 0.27, 0.07, 0.6)
				imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.55, 0.27, 0.07, 1.0)
			
			if piece != 0:
				# imgui.push_style_color(imgui.COLOR_BUTTON, 0.87, 0.72, 0.53, 1.0)  # Light brown
				# imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.87, 0.72, 0.53, 0.6)
				# imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.87, 0.72, 0.53, 1.0)
				imgui.image_button(textures[piece].texture_id, size, size)
				if imgui.is_item_hovered() and imgui.is_mouse_clicked():
					PressedButton(x, y)
			else:
				imgui.internal.push_item_flag(imgui.internal.ITEM_DISABLED, True)
				imgui.image_button(textures[0].texture_id, size, size)
				imgui.internal.pop_item_flag()
			
			imgui.pop_style_color(3)

			x_c += delta

		y_c += delta
		x_c = x_s


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

	board = Board()

	# MAIN LOOP
	while not glfw.window_should_close(window):
		glfw.poll_events()
		impl.process_inputs()

		imgui.new_frame()

		imgui.begin("Board")
		imgui.set_window_size(500, 500)
		draw_board(
			board,
			imgui.get_cursor_pos(),
			imgui.get_content_region_available()
		)
		imgui.end()

		# Top menu bar
		if imgui.begin_main_menu_bar():
			clicked, _ = imgui.menu_item("Toggle settings", "Ctrl+,", False)
			if clicked:
				show_settings = not show_settings
			imgui.end_main_menu_bar()

		if show_settings:
			_, show_settings = imgui.begin("Settings", True, imgui.WINDOW_NO_COLLAPSE)
			imgui.set_window_size(300, 200)

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