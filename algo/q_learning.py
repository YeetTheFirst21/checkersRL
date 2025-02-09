
import torch
import torch.nn as nn
import torch.nn.functional as F

import copy
import pathlib
from dataclasses import dataclass

from . import iplayer
from .board import Board, GameState

class QLearning(iplayer.IPlayer):
	class DQN(nn.Module):
		GAMMA = 0.99 # discount rate

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
			state = board.to_tensor(self.device)
			for layer in self.layers[:-1]:
				state = F.relu(layer(state))
			return self.layers[-1](state)
	
	@dataclass
	class Action:
		action: tuple[tuple[int, int], tuple[int, int]]
		value: torch.Tensor
		
	def __init__(self, model_path: str = "dqn.pth", layer_sizes: list[int] = [90, 50, 50, 1]) -> None:
		super().__init__()

		self.__model_path = model_path
		self.__layer_sizes = layer_sizes
		self.__model_file_name = pathlib.Path(model_path).name

		self.device = torch.device("cpu")
		self.model = self.DQN(device=self.device, layer_sizes=layer_sizes)
		self.model.load_state_dict(torch.load(model_path))
	
	def decide_move(self, board: Board) -> tuple[tuple[int, int], tuple[int, int]]:
		ret: list[QLearning.Action] = []
		for s in board.get_possible_pos():
			for e in board.get_correct_moves(s):
				next_state = copy.deepcopy(board)
				immediate_reward = torch.tensor([bool(next_state.make_move(s, e).captured) * next_state.turn_sign], device=self.device)
				value = self.model(next_state) * self.DQN.GAMMA + immediate_reward
				ret.append(QLearning.Action((s, e), value))
		return max(ret, key=lambda x: x.value.item()).action

	def __str__(self) -> str:
		return f"{self.__model_file_name} ({self.__layer_sizes})"