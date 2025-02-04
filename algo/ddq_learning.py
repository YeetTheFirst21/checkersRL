import torch
import torch.nn as nn
import torch.nn.functional as F

import copy
from dataclasses import dataclass

from . import iplayer
from .board import Board, GameState, MoveResult

class QLearning(iplayer.IPlayer):
	class DQN(nn.Module):
		GAMMA = 0.99 # discount rate

		"""
		def __init__(self):
		super(DQN, self).__init__()

		layer_sizes = [
			90,
			50,
			50,
			1
		]

		layers = []
		prev_size = layer_sizes[0]
		for cur_size in layer_sizes[1:]:
			layer = nn.Linear(prev_size, cur_size)
			# nn.init.kaiming_uniform(layer.weight, nonlinearity='relu')
			layers.append(layer)
			prev_size = cur_size

		self.layers = nn.ModuleList(layers)

	def forward(self, board: Board) -> torch.Tensor:
		state = board.to_tensor(
			device,
			board.turn_sign != DEPLOYMENT_SIGN
		)
		for layer in self.layers[:-1]:
			state = F.relu(layer(state))
		return self.layers[-1](state)
		"""

		def __init__(self, device, layer_sizes: list[int]):
			super(QLearning.DQN, self).__init__()

			layers = []
			prev_size = layer_sizes[0]
			for cur_size in layer_sizes[1:]:
				layers.append(nn.Linear(prev_size, cur_size))
				prev_size = cur_size

			self.layers = nn.ModuleList(layers)
			self.device = device

		def forward(self, board: Board) -> torch.Tensor:
			state = board.to_tensor(
				self.device,
				board.turn_sign != -1
			)
			for layer in self.layers[:-1]:
				state = F.relu(layer(state))
			return self.layers[-1](state)
	
	@dataclass
	class Action:
		action: tuple[tuple[int, int], tuple[int, int]]
		value: torch.Tensor
		
	def __init__(self, model_path: str = "ddqn87 90 50 50 1 q_1 tuned on ddqn86.pth", layer_sizes: list[int] = [90, 50, 50, 1]) -> None:
		super().__init__()

		self.__model_path = model_path
		self.__layer_sizes = layer_sizes

		self.device = torch.device("cpu")
		self.model = self.DQN(device=self.device, layer_sizes=layer_sizes)
		self.model.load_state_dict(torch.load(model_path))

	@staticmethod
	def move_result_to_reward(move_result: MoveResult) -> float:
		return move_result.captured + move_result.promoted * 2

	@staticmethod
	def state_to_reward(state: Board) -> float:
		return -2 * (state.moves_since_last_capture > 5)
	
	def decide_move(self, board: Board) -> tuple[tuple[int, int], tuple[int, int]]:
		ret: list[QLearning.Action] = []
		for s in board.get_possible_pos():
			for e in board.get_correct_moves(s):
				next_state = copy.deepcopy(board)
				immediate_reward = torch.tensor([
					self.move_result_to_reward(next_state.make_move(s, e)) + 
					self.state_to_reward(next_state)
				], device=self.device)
				value = self.model(next_state) * self.DQN.GAMMA + immediate_reward
				ret.append(self.Action((s, e), value))
		return max(ret, key=lambda x: x.value.item()).action

	def __str__(self) -> str:
		return f"DDQN {self.__layer_sizes} {self.__model_path}"