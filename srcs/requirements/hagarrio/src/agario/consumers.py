import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .Game import Game
import uuid
import asyncio
from .logger import setup_logger

logger = setup_logger()

class GameConsumer(AsyncWebsocketConsumer):
	players = {}  # {player_id: websocket}
	active_games = {}  # {game_id: Game()}
	player_count = 0

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.player_id = None
		self.current_game_id = None

	async def connect(self):
		await self.accept()
		self.player_id = str(uuid.uuid4())
		GameConsumer.player_count += 1
		self.player_name = f"Player_{GameConsumer.player_count}"
		GameConsumer.players[self.player_id] = self

		# Envoyer la liste des parties disponibles
		await self.send_games_info()

	async def disconnect(self, close_code):
		logger.info(f"Player {self.player_id} disconnected with code {close_code}")
		
		if self.player_id in GameConsumer.players:
			GameConsumer.player_count -= 1
			del GameConsumer.players[self.player_id]
			logger.debug(f"Removed player {self.player_id} from players list")

		if self.current_game_id in GameConsumer.active_games:
			game = GameConsumer.active_games[self.current_game_id]
			# Informer les autres joueurs de la déconnexion immédiatement
			for player_id in game.players:
				if player_id != self.player_id and player_id in GameConsumer.players:
					await GameConsumer.players[player_id].send(text_data=json.dumps({
						'type': 'player_disconnected',
						'playerId': self.player_id
					}))
			game.remove_player(self.player_id)
			logger.debug(f"Removed player {self.player_id} from game {self.current_game_id}")

			# Si la partie est vide, on la nettoie et la supprime
			if len(game.players) == 0:
				logger.info(f"Game {self.current_game_id} is empty, cleaning up")
				await game.cleanup()
				del GameConsumer.active_games[self.current_game_id]
				for player_id in GameConsumer.players:
					games_info = []
					for game_id, game in GameConsumer.active_games.items():
						games_info.append({
							'gameId': game_id,
							'players': [{'name': p['name'], 'id': p['id']} for p in game.players.values()] ,
							'status': game.status
					})
					await GameConsumer.players[player_id].send(text_data=json.dumps({
						'type': 'player_disconnected',
						'games': games_info,
						'playerId': self.player_id
					}))
			else:
				# Informer les autres joueurs de la déconnexion
				logger.debug(f"Broadcasting updated game info after player disconnect")
				await self.broadcast_games_info_waitingroom()
				
				# Si la partie n'a plus qu'un joueur, on met à jour son statut
				if len(game.players) == 1:
					game.status = "custom"
					logger.info(f"Game {self.current_game_id} returned to custom status")

	async def receive(self, text_data):
		data = json.loads(text_data)
		
		if data['type'] == 'start_game':
			# Créer une nouvelle partie
			new_game = Game(str(uuid.uuid4()))
			GameConsumer.active_games[new_game.game_id] = new_game
			self.current_game_id = new_game.game_id
			new_game.add_player(self.player_id, self.player_name)
			
			# Démarrer la boucle de jeu
			await new_game.start_game_loop(self.broadcast_game_state)
			await self.broadcast_games_info_waitingroom()
			
			# Envoyer l'état initial au créateur
			await self.send(text_data=json.dumps({
				'type': 'game_started',
				'gameId': new_game.game_id,
				'mapWidth': new_game.map_width,
				'mapHeight': new_game.map_height,
				'maxFood': new_game.max_food,
				'players': new_game.players,
				'food': new_game.food,
				'yourPlayerId': self.player_id
			}))

		elif data['type'] == 'join_game':
			game_id = data['gameId']
			if game_id in GameConsumer.active_games:
				game = GameConsumer.active_games[game_id]
				if game.status == "custom":
					self.current_game_id = game_id
					game.add_player(self.player_id, self.player_name)
					await self.broadcast_games_info_waitingroom()
					
					# Envoyer l'état initial au joueur qui rejoint
					await self.send(text_data=json.dumps({
						'type': 'game_joined',
						'gameId': game_id,
						'mapWidth': game.map_width,
						'mapHeight': game.map_height,
						'maxFood': game.max_food,
						'players': game.players,
						'food': game.food,
						'yourPlayerName': self.player_name,
						'yourPlayerId': self.player_id
					}))

		elif data['type'] == 'input':
			if self.current_game_id in GameConsumer.active_games:
				game = GameConsumer.active_games[self.current_game_id]
				game.handle_player_input(self.player_id, data['key'], data['isKeyDown'])

		elif data['type'] == 'use_power_up':
			if self.current_game_id in GameConsumer.active_games:
				game = GameConsumer.active_games[self.current_game_id]
				game.use_power_up(self.player_id, data['slot'])

	async def send_games_info(self):
		"""Envoie la liste des parties disponibles à tous les joueurs"""
		games_info = []
		for game_id, game in GameConsumer.active_games.items():
			games_info.append({
				'gameId': game_id,
				'players': [{'name': p['name'], 'id': p['id']} for p in game.players.values()] ,
				'status': game.status
			})

		await self.send(text_data=json.dumps({
			'type': 'waiting_room',
			'games': games_info,
			'yourPlayerId': self.player_id,
			'yourPlayerName': self.player_name
		}))

	async def broadcast_games_info_waitingroom(self):
		"""Diffuse les informations sur les parties à tous les joueurs"""
		games_info = []
		for game_id, game in GameConsumer.active_games.items():
			games_info.append({
				'gameId': game_id,
				'players': [{'name': p['name'], 'id': p['id']} for p in game.players.values()] ,
				'status': game.status
			})

		for player in GameConsumer.players.values():
			await player.send(text_data=json.dumps({
				'type': 'update_waiting_room',
				'games': games_info,
				'players': game.players
			}))

	async def broadcast_game_state(self, game_id, state_update):
		"""Diffuse les mises à jour du jeu aux joueurs"""
		if game_id in GameConsumer.active_games:
			game = GameConsumer.active_games[game_id]
			message = {
				'type': state_update['type'],
				'game_id': state_update['game_id'],
				'players': state_update['players'],
				'yourPlayerName': game.players[self.player_id]['name'],
				'yourPlayerId': self.player_id
			}
			# Détermine le type de mise à jour explicitement
			if state_update['type'] == 'food_update':
				message.update({'food': state_update['food']})
			elif state_update['type'] == 'power_up_spawned':
				message.update({
					'power_up': state_update['power_up'],
					'power_ups': state_update['power_ups']
				})
			elif state_update['type'] == 'power_up_collected':
				message.update({
					'power_up': state_update['power_up'],
					'power_ups': state_update['power_ups']
				})
			elif state_update['type'] == 'power_up_used':
				message.update({
					'power_up': state_update['power_up']
				})
			elif state_update['type'] == 'player_eat_other_player':
				eaten_player_id = state_update['other_player_id']
				# Envoyer d'abord la notification aux joueurs restants
				for player_id in game.players:
					if player_id in GameConsumer.players:
						await GameConsumer.players[player_id].send(text_data=json.dumps({
							'type': 'player_eat_other_player',
							'game_id': game_id,
							'players': game.players,
							'player_eaten': eaten_player_id
						}))
				
				# Gérer le joueur mangé séparément
				if eaten_player_id in GameConsumer.players:
					eaten_player = GameConsumer.players[eaten_player_id]
					eaten_player.current_game_id = None
					
					# Renvoyer le joueur mangé à la waiting room
					await eaten_player.send(text_data=json.dumps({
						'type': 'return_to_waiting_room',
						'message': f'Score final : {state_update.get("score", 0):.0f}'
					}))
					await eaten_player.send_games_info()
					
				return  # Sortir de la fonction pour éviter l'envoi multiple

			# Envoie la mise à jour à tous les joueurs de la partie
			for player_id in game.players:
				if player_id in GameConsumer.players:
					await GameConsumer.players[player_id].send(text_data=json.dumps(message))

	#TODO: Gérer les nouvelles parties avec matchmaking
	# async def new_game(game_id, player_excepted):
	# 	new_game = Game(game_id)
	# 	GameConsumer.active_games[new_game.game_id] = new_game