import imgui

from .ui_state import UIState
from algo.iplayer import IPlayer, IRandomPlayer, ITrainablePlayer

class ModelsMenu:
	def __init__(self, state: UIState) -> None:
		self.state = state
		self.show_window: bool = True

		self.selected_model = 1

		self.__all_training_seeds_input = 0

		self.training_steps = 500
		self.training_enemy_index = state.player_i[-1]

	def reset_seeds(self) -> None:
		for player in self.state.players:
			if isinstance(player, IRandomPlayer):
				player.seed = self.__all_training_seeds_input

	def draw(self):
		if not self.show_window:
			return
		
		with imgui.begin("Models menu", True) as (_, is_open):
			imgui.set_window_size(400, 600)
			self.show_window = is_open

			imgui.text("Model:")
			imgui.same_line()
			imgui.set_next_item_width(-1)
			_, self.selected_model = imgui.combo("##worked_on_model", self.selected_model, [
				self.state.get_player_list_name(i) for i in range(len(self.state.players))
			])
			
			if imgui.button("Reset all seeds"):
				self.reset_seeds()

			imgui.same_line()
			imgui.set_next_item_width(-1)
			_, self.__all_training_seeds_input = imgui.input_int(
				"##all_training_seeds_input", self.__all_training_seeds_input)


			selected_model = self.state.players[self.selected_model]

			if isinstance(selected_model, ITrainablePlayer):
				imgui.separator()
				imgui.text("Training section:")
				imgui.text("Enemy:")
				imgui.same_line()
				imgui.set_next_item_width(-1)
				_, self.training_enemy_index = imgui.combo("##training_enemy", self.training_enemy_index, [
					self.state.get_player_list_name(i) for i in range(len(self.state.players))
				])

				_, self.training_steps = imgui.input_int(
					"##training_steps", self.training_steps)
				
				imgui.same_line()
				if imgui.button("Do training"):
					for i in range(self.training_steps):
						selected_model.do_training_round(self.state.players[self.training_enemy_index], 1)
						selected_model.do_training_round(self.state.players[self.training_enemy_index], -1)
					
					selected_model.save_model("")

			imgui.separator()
			imgui.text(f"{self.state.get_player_list_name(self.selected_model)} parameters:")

			if isinstance(selected_model, IRandomPlayer):
				imgui.text("Randomness:")
				imgui.set_next_item_width(imgui.get_content_region_available_width() * 0.4)
				changed, new_seed = imgui.input_int("Seed", selected_model.seed)
				if changed:
					selected_model.seed = new_seed
				
				imgui.same_line()
				if imgui.button("Reset seed"):
					selected_model.seed = 0
