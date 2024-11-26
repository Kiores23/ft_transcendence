# run_ia.py
from .ia import IA
import websocket
from .logger import logger

def run_ia(data):
    game_id = data['game_id']
    ai_id = data['ai_id']
    logger.debug(f"RUN IA : {data}")
    host = 'pong'  # Ou l'adresse IP de votre serveur
    port = '8000'       # Changez le port si nécessaire
    websocket_url = f"ws://{host}:{port}/ws/pong/{game_id}/{ai_id}/"
    logger.debug(f"WS URL : {websocket_url}")
    
    ia = IA()
    


    ws = websocket.WebSocketApp(websocket_url,
                                on_open=ia.on_open,
                                on_message=ia.on_message,
                                on_error=ia.on_error,
                                on_close=ia.on_close)
    logger.debug("LOPETICHA")
    
    ws.run_forever()
