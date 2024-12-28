import { Link } from 'react-router-dom';
import logo from '../elements/logo.png';
import { useNavigate, useLocation } from "react-router-dom";
import { useEffect } from "react";


export default function InGame() {
    const navigate = useNavigate();
    const location = useLocation();
    
    const { gameService, gameId } = location.state || {}; // Récupérer les données transmises via navigation

      useEffect(() => {
        try {
            if (!gameService || !gameId) {
                console.error("Missing or invalid gameService or gameId");
                navigate("/pong");
                return;
            }
          
            const existingIframe = document.querySelector('#gameFrame');
            if (existingIframe) {
                existingIframe.remove(); // Nettoyer toute iframe existante
            }
          
            const iframe = document.createElement('iframe');
            iframe.id = "gameFrame";
            iframe.src = `${gameService}/?gameId=${gameId}`;
            iframe.style.position = "fixed";
            iframe.style.top = "75px";
            iframe.style.left = "0";
            iframe.style.width = "100vw";
            iframe.style.height = "93vh";
            iframe.style.border = "none";
            iframe.style.zIndex = "9999";
            iframe.scrolling = "no";
            iframe.sandbox = "allow-scripts allow-same-origin";
            // Ajouter l'iframe au DOM
            document.body.appendChild(iframe)

        } catch (error) {
            console.error("Error during iframe setup:", error);
            navigate("/pong");
        }
      
        return () => {
            const iframe = document.querySelector('#gameFrame');
            if (iframe) {
                iframe.remove();
            }
        };
    }, []);
  

    const Cancel = async () => {
        const iframe = document.querySelector('#gameFrame');
        if (iframe) {
            iframe.contentWindow.postMessage('stop_game', '*');
            await new Promise(resolve => setTimeout(resolve, 100));
            iframe.remove();
        }
        navigate("/pong");
    };

    return (
        <div>
            <div className="topnav">
                <Link className="active"><img className="logo" src={logo} alt="Logo" /></Link>
                <button 
                    className="exit-button btn btn-outline-warning" 
                    type="button" 
                    onClick={Cancel}
                >
                    EXIT
                </button>
                <h1 className="wait">Wait for the game to load</h1>
            </div>
            <div id="iframe-container" style={{ marginTop: '20px' }}>
            </div>
        </div>
    );
}
