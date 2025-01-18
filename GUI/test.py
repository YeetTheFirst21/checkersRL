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
import os
from PIL import Image

C = 0.01
L = int(pi * 2 * 100)
# this is our 6*6 board where 0 is nothing, 1 is black, -1 is white 2 is black king and -2 is white king. 
gameBoard = np.array([
	[-1, 0, -1, 0, -2, 0],
	[0, -1, 0, -1, 0, -1],
	[0, 0, 0, 0, 0, 0],
	[0, 0, 0, 0, 0, 0],
	[1, 0, 1, 0, 1, 0],
	[0, 1, 0, 1, 0, 2]
]).T

pressedButton = [0, 0]

def load_texture(file_path):
	try:
		# Get the directory of the current file
		current_dir = os.path.dirname(os.path.abspath(__file__))
		full_path = os.path.join(current_dir, file_path)

		image = Image.open(full_path)
		image = image.transpose(Image.FLIP_TOP_BOTTOM)
		img_data = image.convert("RGBA").tobytes()
		width, height = image.size

		texture_id = gl.glGenTextures(1)
		gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
		gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img_data)
		gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
		gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
		gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

		return texture_id
	except Exception as e:
		print(f"Failed to load texture {file_path}: {e}")
		return None

def PressedButton(i, j):
	print(f"Button at {i}, {j}) pressed")


def __draw_board() -> None:
    size = (min(*imgui.get_content_region_available()) - 50) / 6
    for j in range(6):
        for i in range(6):
            imgui.same_line()

            if gameBoard[i][j] == -1:  # -1 is top of the board and black
                imgui.push_style_color(imgui.COLOR_BUTTON, 0.87, 0.72, 0.53, 1.0)  # Light brown
                imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.87, 0.72, 0.53, 0.6)
                imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.87, 0.72, 0.53, 1.0)

                imgui.image_button(black_circle, size, size)
                if imgui.is_item_hovered() and imgui.is_mouse_clicked():
                    PressedButton(i, j)
            elif gameBoard[i][j] == -2:
                imgui.push_style_color(imgui.COLOR_BUTTON, 0.87, 0.72, 0.53, 1.0)  # Light brown
                imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.87, 0.72, 0.53, 0.6)
                imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.87, 0.72, 0.53, 1.0)

                imgui.image_button(black_king, size, size)
                if imgui.is_item_hovered() and imgui.is_mouse_clicked():
                    PressedButton(i, j)
            elif gameBoard[i][j] == 1:  # 1 is bottom of the board and white
                imgui.push_style_color(imgui.COLOR_BUTTON, 0.87, 0.72, 0.53, 1.0)  # Light brown
                imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.87, 0.72, 0.53, 0.6)
                imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.87, 0.72, 0.53, 1.0)

                imgui.image_button(white_circle, size, size)
                if imgui.is_item_hovered() and imgui.is_mouse_clicked():
                    PressedButton(i, j)
            elif gameBoard[i][j] == 2:
                imgui.push_style_color(imgui.COLOR_BUTTON, 0.87, 0.72, 0.53, 1.0)  # Light brown
                imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.87, 0.72, 0.53, 0.6)
                imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.87, 0.72, 0.53, 1.0)

                imgui.image_button(white_king, size, size)
                if imgui.is_item_hovered() and imgui.is_mouse_clicked():
                    PressedButton(i, j)
            else:
                # Check if in diagonal to paint diagonals dark brown and rest light brown:
                if (i + j) % 2 == 0:
                    imgui.push_style_color(imgui.COLOR_BUTTON, 0.87, 0.72, 0.53, 1.0)  # Light brown
                    imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.87, 0.72, 0.53, 0.6)
                    imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.87, 0.72, 0.53, 1.0)
                else:
                    imgui.push_style_color(imgui.COLOR_BUTTON, 0.55, 0.27, 0.07, 1.0)  # Dark brown
                    imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.55, 0.27, 0.07, 0.6)
                    imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.55, 0.27, 0.07, 1.0)
                imgui.internal.push_item_flag(imgui.internal.ITEM_DISABLED, True)
                imgui.image_button(nothing, size, size)
                imgui.internal.pop_item_flag()
                imgui.pop_style_color(3)
                continue
            imgui.pop_style_color(3)

        imgui.new_line()

def main():
	window = __impl_glfw_init()
	imgui.create_context()
	impl = GlfwRenderer(window)

	# Load textures
	global black_circle, black_king, white_circle, white_king, nothing
	black_circle = load_texture("black_circle.png")
	black_king = load_texture("black_king.png")
	white_circle = load_texture("white_circle.png")
	white_king = load_texture("white_king.png")
	nothing = load_texture("nothing.png")

	plot_values = array("f", [sin(x * C) for x in range(L)])
	histogram_values = array("f", [random() for _ in range(20)])

	while not glfw.window_should_close(window):
		glfw.poll_events()
		impl.process_inputs()

		# setting window size before creating a new frame or else it will be stuck at that size
		imgui.set_window_size_named("Checkers", 440, 420)

		# this is where the code gets recalled every time you run it
		imgui.new_frame()

		imgui.begin("Checkers", flags=imgui.WINDOW_NO_SCROLLBAR)
		__draw_board()
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