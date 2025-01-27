from PIL import Image
import OpenGL.GL as gl
import imgui

import pathlib
from collections.abc import Callable
from typing import Optional


ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve().absolute()

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
		full_path = (ROOT_DIR / path).resolve().absolute()

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
		

class disabled_block:
	# https://github.com/ocornut/imgui/issues/1889#issuecomment-398681105
	def __init__(self, is_disabled = True) -> None:
		self.is_disabled = is_disabled

	def __enter__(self) -> None:
		if self.is_disabled:
			imgui.internal.push_item_flag(imgui.internal.ITEM_DISABLED, self.is_disabled)
			imgui.push_style_var(imgui.STYLE_ALPHA, 0.5)
	
	def __exit__(self, exc_type, exc_value, traceback) -> None:
		if self.is_disabled:
			imgui.pop_style_var()
			imgui.internal.pop_item_flag()