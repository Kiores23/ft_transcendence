from django.db import models
from django.db import IntegrityError, DatabaseError
from django.core.exceptions import ValidationError
from django.utils import timezone
from .utils.logger import logger

class Player(models.Model):
	STATUS_CHOICES = [
		('inactive', 'Player is inactive or not engaged in any activity'),
		('in_queue', 'Player is in a matchmaking queue'),
		('pending', 'Player is expected to join a game'),
		('waiting_for_players', 'Player is waiting for other players to join the game'),
		('loading_game', 'Player is waiting for the game to load'),
		('in_game', 'Player is currently playing in a game'),
		('spectate', 'Player is currently spectating a game'),
		('in_private_room', 'Player is currently in a private room'),
	]

	username = models.CharField(max_length=100, unique=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
	game_history = models.JSONField(default=list)  # Stocke l'historique sous forme de liste JSON (ID de parties par exemple)

	def __str__(self):
		return self.username

	# Méthode pour créer un joueur
	@classmethod
	def get_or_create_player(cls, username):
		try:
			player, created = cls.objects.get_or_create(username=username)
			if created:
				logger.debug(f'{player.username} game acount created')
			return player
		except IntegrityError as e:
			logger.error(f"Integrity error while creating player: {e}")
			return None
		except DatabaseError as e:
			logger.error(f"Database error while creating player: {e}")
			return None

	# Méthode pour ajouter une partie à l'historique du joueur
	def add_game_to_history(self, game_id):
		self.game_history.append(game_id)
		self.save()

	# Méthode pour récupérer l'historique du joueur
	def get_game_history(self):
		return self.game_history

	# Méthode pour modifier le statut du joueur
	def update_status(self, new_status):
		if new_status in dict(self.STATUS_CHOICES):
			self.status = new_status
			self.save()
		else:
			raise ValueError(f"Invalid status: {new_status}")

class GameInstance(models.Model):
	STATUS_CHOICES = [
		('waiting', 'Waiting for players to join'),
		('loading', 'Players are loading game assets and configurations'),
		('in_progress', 'Game currently in progress'),
		('aborted', 'Game has been aborted'),
		('finished', 'Game has finished'),
	]


	game_id = models.CharField(max_length=100, unique=True)  # ID de la partie
	usernames = models.JSONField()  # Tableau avec les usernames des joueurs
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')  # Statut de la partie
	scores = models.JSONField(default=dict)  # Dictionnaire des scores par équipe
	winner = models.CharField(max_length=20, blank=True, null=True)  # Vainqueur (team) s'il y en a un
	game_date = models.DateTimeField(default=timezone.now)  # Date de la partie
	game_mode = models.CharField(max_length=20)  # Mode de jeu
	teams = models.JSONField(default=dict)  # Dictionnaire pour stocker les équipes et les joueurs

	def __str__(self):
		return f"Game {self.game_id} - Status: {self.status} - Mode: {self.game_mode}"

	def is_finished(self):
		"""Vérifie si la partie est terminée."""
		return self.status in ['finished', 'aborted']

	def clean(self):
		"""Validation pour l'unicité des usernames."""
		if len(self.usernames) != len(set(self.usernames)):
			raise ValidationError("Usernames must be unique.")

	def save(self, *args, **kwargs):
		self.clean()  # Appeler la validation avant de sauvegarder
		super(GameInstance, self).save(*args, **kwargs)

	def update_score(self, team, score):
		"""Met à jour le score de l'équipe spécifiée."""
		if team not in self.teams:
			self.teams[team] = []
		self.scores[team] = score
		self.save()  # Sauvegarde les modifications

	def set_winner(self, team):
		"""Définit l'équipe gagnante et met à jour le statut de la partie."""
		self.winner = team
		self.save()  # Sauvegarde les modifications

	def update_status(self, new_status):
		if new_status in dict(self.STATUS_CHOICES):
			self.status = new_status
			self.save()
		else:
			raise ValueError(f"Invalid status: {new_status}")

	def abort_game(self):
		"""Met à jour le statut de la partie à 'aborted'."""
		self.status = 'aborted'
		self.save()

	@classmethod
	def create_game(cls, game_id, game_mode, usernames):
		try:
			new_game = cls(
				game_id=game_id,
				usernames=usernames,
				status='waiting',
				scores={},
				winner=None,
				game_mode=game_mode,
				teams={}
			)
			new_game.save()
			return new_game
		except IntegrityError as e:
			logger.error(f"Integrity error while creating game: {e}")
			return None
		except DatabaseError as e:
			logger.error(f"Database error while creating game: {e}")
			return None

	@classmethod
	def get_game(cls, game_id):
		try:
			return cls.objects.get(game_id=game_id)
		except cls.DoesNotExist:
			return None

	def add_player_to_team(self, player, team_name):
		if team_name not in self.teams:
			self.teams[team_name] = []
		self.teams[team_name].append(player)
		self.save()
