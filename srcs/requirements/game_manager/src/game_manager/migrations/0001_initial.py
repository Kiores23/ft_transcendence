# Generated by Django 4.2.7 on 2024-11-07 08:22

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GameInstance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('game_id', models.CharField(max_length=100, unique=True)),
                ('usernames', models.JSONField()),
                ('status', models.CharField(choices=[('waiting', 'Waiting for players to join'), ('loading', 'Players are loading game assets and configurations'), ('in_progress', 'Game currently in progress'), ('aborted', 'Game has been aborted'), ('finished', 'Game has finished')], default='waiting', max_length=20)),
                ('scores', models.JSONField(default=dict)),
                ('winner', models.CharField(blank=True, max_length=20, null=True)),
                ('game_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('game_mode', models.CharField(max_length=20)),
                ('teams', models.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=100, unique=True)),
                ('status', models.CharField(choices=[('inactive', 'Player is inactive or not engaged in any activity'), ('in_queue', 'Player is in a matchmaking queue'), ('pending', 'Player is expected to join a game'), ('waiting_for_players', 'Player is waiting for other players to join the game'), ('loading_game', 'Player is waiting for the game to load'), ('in_game', 'Player is currently playing in a game'), ('spectate', 'Player is currently spectating a game'), ('in_private_room', 'Player is currently in a private room')], default='inactive', max_length=20)),
                ('game_history', models.JSONField(default=list)),
            ],
        ),
    ]
