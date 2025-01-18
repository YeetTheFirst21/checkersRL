# https://github.com/pyimgui/pyimgui/blob/master/doc/examples/plots.py

import os
import sys
import pathlib
from typing import Optional

import glfw
import OpenGL.GL as gl
import imgui
from imgui.integrations.glfw import GlfwRenderer
from PIL import Image


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
		if self.texture_id is not None:
			gl.glDeleteTextures(self.texture_id)


def __draw_board() -> None:
	width, height = imgui.get_content_region_available()
	cell_width = width / 6
	cell_height = height / 6
	for i in range(6):
		for j in range(6):
			imgui.same_line()
			imgui.image_button(test.texture_id, cell_width, cell_height)
		imgui.new_line()


def main():
	window = __impl_glfw_init()
	imgui.create_context()
	impl = GlfwRenderer(window)

	# INIT STAGE
	show_settings = True
	imgui.get_io().font_global_scale = 1.5

	global test
	test = ImageTexture("./icons/test.png")

	# MAIN LOOP
	while not glfw.window_should_close(window):
		glfw.poll_events()
		impl.process_inputs()

		imgui.new_frame()

		imgui.begin("Plot example")
		__draw_board()
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