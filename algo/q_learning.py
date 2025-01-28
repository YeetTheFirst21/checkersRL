
import torch
import torch.nn as nn
import torch.nn.functional as F

import copy
from dataclasses import dataclass

from . import iplayer
from .board import Board, GameState

class QLearning(iplayer.IPlayer):
	class DQN(nn.Module):
		GAMMA = 0.99 # discount rate

		def __init__(self, device):
			super(QLearning.DQN, self).__init__()

			layer_sizes = [
				90,
				20,
				1
			]

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
		
	def __init__(self, model_path: str = "dqn.pth") -> None:
		super().__init__()
		self.device = torch.device("cpu")
		self.model = self.DQN(device=self.device)
		self.model.load_state_dict(torch.load(model_path))
	
	def decide_move(self, board: Board) -> tuple[tuple[int, int], tuple[int, int]]:
		ret: list[QLearning.Action] = []
		for s in board.get_possible_pos():
			for e in board.get_correct_moves(s):
				next_state = copy.deepcopy(board)
				immediate_reward = torch.tensor([next_state.make_move(s, e) * next_state.turn_sign], device=self.device)
				value = self.model(next_state) * self.DQN.GAMMA + immediate_reward
				ret.append(QLearning.Action((s, e), value))
		return max(ret, key=lambda x: x.value.item()).action