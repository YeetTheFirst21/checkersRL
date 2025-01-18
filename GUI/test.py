#!/usr/bin/env python
# -*- coding: utf-8 -*-

from array import array
from imgui.integrations.glfw import GlfwRenderer
from math import sin, pi
from random import random
from time import time
import OpenGL.GL as gl
import glfw
import imgui
import sys
import numpy as np

C = 0.01
L = int(pi * 2 * 100)
# this is our 6*6 board where 0 is nothing, 1 is black, -1 is white 2 is black king and -2 is white king. 
gameBoard = np.array([
	[-1, 0, -1, 0, -1, 0],
	[0, -1, 0, -1, 0, -1],
	[0, 0, 0, 0, 0, 0],
	[0, 0, 0, 0, 0, 0],
	[1, 0, 1, 0, 1, 0],
	[0, 1, 0, 1, 0, 1]
]).T

pressedButton = [0, 0]



#def __draw_board(fontObject) -> None:
def __draw_board() -> None:
	size = (min(*imgui.get_content_region_available())-50) / 6
	for j in range(6):
		for i in range(6):
			imgui.same_line()

			def PressedButton(x, y):
				print(f"Button at ({x}, {y}) pressed")

			if gameBoard[ i ][ j ] == -1:# -1 is top of the board and black
				imgui.push_style_color(imgui.COLOR_BUTTON, 1.0, 0.0, 0.0, 1.0)
				imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 1.0, 0.0, 0.0, 0.6)
				imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.0, 0.0, 0.0, 1.0)

				if imgui.button("u" + f"##{i},{j}", size, size):
					PressedButton(i, j)
			elif gameBoard[ i ][ j ] == -2:
				imgui.push_style_color(imgui.COLOR_BUTTON, 1.0, 0.0, 0.0, 1.0)
				imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 1.0, 0.0, 0.0, 0.6)
				imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.0, 0.0, 0.0, 1.0)
				
				if imgui.button(f"##{i},{j}", size, size):
					PressedButton(i, j)
			elif gameBoard[ i ][ j ] == 1:# 1 is bottom of the board and white
				imgui.push_style_color(imgui.COLOR_BUTTON, 1.0, 1.0, 1.0, 1.0)
				imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 1.0, 1.0, 1.0, 0.6)
				imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 1.0, 1.0, 1.0, 1.0)

				if imgui.button(f"##{i},{j}", size, size):
					PressedButton(i, j)
			elif gameBoard[ i ][ j ] == 2:
				imgui.push_style_color(imgui.COLOR_BUTTON, 1.0, 1.0, 1.0, 1.0)
				imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 1.0, 1.0, 1.0, 0.6)
				imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 1.0, 1.0, 1.0, 1.0)

				if imgui.button(f"##{i},{j}", size, size):
					PressedButton(i, j)
			else:
				#check if in diagonal to paint diagonals white and rest black:
				if (i+j)%2 == 0:
					imgui.push_style_color(imgui.COLOR_BUTTON, 1.0, 1.0, 1.0, 1.0)
					imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 1.0, 1.0, 1.0, 0.6)
					imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 1.0, 1.0, 1.0, 1.0)
				else:
					imgui.push_style_color(imgui.COLOR_BUTTON, 0.4, 0.3, 0.3, 1.0)
					imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.0, 0.0, 0.0, 0.6)
					imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.0, 0.0, 0.0, 1.0)
				imgui.internal.push_item_flag(imgui.internal.ITEM_DISABLED, True)
				if imgui.button(f"##{i},{j}", size, size):
					print(f"Button at ({i}, {j}) pressed")
				imgui.internal.pop_item_flag()
				imgui.pop_style_color(3)
				continue
			imgui.pop_style_color(3)

		imgui.new_line()


def main():
	window = __impl_glfw_init()
	imgui.create_context()
	impl = GlfwRenderer(window)


	plot_values = array("f", [sin(x * C) for x in range(L)])
	histogram_values = array("f", [random() for _ in range(20)])

	while not glfw.window_should_close(window):
		glfw.poll_events()
		impl.process_inputs()

		# import os
		# # Load the font
		# font_file_name = "CourierNew.ttf"#"DejaVuSans.ttf"
		# font_file_path = os.path.join(os.path.dirname(__file__), font_file_name)

		# # check if the font file exists
		# try:
		# 	with open(font_file_path, "rb") as f:
		# 		pass
		# except FileNotFoundError:
		# 	print(f"Font file not found: {font_file_path}")
		# 	sys.exit(1)


		# font_pixel_size = 20
		# io = imgui.get_io()
		# new_font = io.fonts.add_font_from_file_ttf(
		# 	font_file_path, font_pixel_size,
		# )

		# impl.refresh_font_texture()



		# setting window size before creating a new frame or else it will be stuck at that size
		imgui.set_window_size_named("Checkers", 400, 415)

		# thşs is where the code gets recalled every time you run it
		imgui.new_frame()

		imgui.begin("Checkers", flags=imgui.WINDOW_NO_SCROLLBAR )
		__draw_board()#new_font)
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
	window_name = "minimal ImGui/GLFW3 example"

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