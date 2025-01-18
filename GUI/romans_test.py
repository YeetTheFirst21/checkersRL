# https://github.com/pyimgui/pyimgui/blob/master/doc/examples/integrations_pysdl2.py

from imgui.integrations.sdl2 import SDL2Renderer
from sdl2 import *
import OpenGL.GL as gl
import ctypes
import imgui.core as imgui
import sys


def main():
	window, gl_context = __impl_pysdl2_init()
	imgui.create_context()
	impl = SDL2Renderer(window)

	show_settings = True
	imgui.get_io().font_global_scale = 1.5

	running = True
	event = SDL_Event()
	while running:
		while SDL_PollEvent(ctypes.byref(event)) != 0:
			if event.type == SDL_QUIT:
				running = False
				break
			impl.process_event(event)
		impl.process_inputs()

		imgui.new_frame()

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
		SDL_GL_SwapWindow(window)

	impl.shutdown()
	SDL_GL_DeleteContext(gl_context)
	SDL_DestroyWindow(window)
	SDL_Quit()



def __impl_pysdl2_init():
	width, height = 1280, 720
	window_name = "minimal ImGui/SDL2 example"

	if SDL_Init(SDL_INIT_EVERYTHING) < 0:
		print(
			"Error: SDL could not initialize! SDL Error: "
			+ SDL_GetError().decode("utf-8")
		)
		sys.exit(1)

	SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
	SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24)
	SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, 8)
	SDL_GL_SetAttribute(SDL_GL_ACCELERATED_VISUAL, 1)
	SDL_GL_SetAttribute(SDL_GL_MULTISAMPLEBUFFERS, 1)
	SDL_GL_SetAttribute(SDL_GL_MULTISAMPLESAMPLES, 8)
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_FLAGS, SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG)
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 4)
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 1)
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE)

	SDL_SetHint(SDL_HINT_MAC_CTRL_CLICK_EMULATE_RIGHT_CLICK, b"1")
	SDL_SetHint(SDL_HINT_VIDEO_HIGHDPI_DISABLED, b"1")

	window = SDL_CreateWindow(
		window_name.encode("utf-8"),
		SDL_WINDOWPOS_CENTERED,
		SDL_WINDOWPOS_CENTERED,
		width,
		height,
		SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE,
	)

	if window is None:
		print(
			"Error: Window could not be created! SDL Error: "
			+ SDL_GetError().decode("utf-8")
		)
		sys.exit(1)

	gl_context = SDL_GL_CreateContext(window)
	if gl_context is None:
		print(
			"Error: Cannot create OpenGL Context! SDL Error: "
			+ SDL_GetError().decode("utf-8")
		)
		sys.exit(1)

	SDL_GL_MakeCurrent(window, gl_context)
	if SDL_GL_SetSwapInterval(1) < 0:
		print(
			"Warning: Unable to set VSync! SDL Error: " + SDL_GetError().decode("utf-8")
		)
		sys.exit(1)

	return window, gl_context


if __name__ == "__main__":
	main()