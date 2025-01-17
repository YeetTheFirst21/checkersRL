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


C = 0.01
L = int(pi * 2 * 100)


def __draw_board() -> None:
	width, height = imgui.get_content_region_available()
	cell_width = width / 6
	cell_height = height / 6
	for i in range(6):
		for j in range(6):
			imgui.same_line()
			imgui.button(f"", cell_width, cell_height)
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

		imgui.new_frame()

		imgui.begin("Plot example")
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