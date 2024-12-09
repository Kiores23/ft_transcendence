from django.urls import path, re_path
from .views import *

urlpatterns = [
	#matchmaking
	re_path(r'^matchmaking/game_mode=(?P<game_mode>.*)/$', get_in_matchmaking, name='matchmaking'),
    path('create_game/', create_game, name='create_game'),
    path('join_game/', join_game, name='create_game'),
    path('create_game_api/', create_game_api, name='create_game_api')
]