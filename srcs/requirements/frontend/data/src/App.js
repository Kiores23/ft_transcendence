import { useState } from 'react';
import HomePage from './pages/HomePage.js'
import AboutPage from './pages/AboutPage.js'
import './assets/App.css';
import NewsPage from './pages/NewsPage.js';
import GameModePage from './pages/GameModesPage.js';
import Leaderboard from './pages/LeaderboardPage.js';
import LoginPage from './pages/LoginPage.js';
import RegisterPage from './pages/RegisterPage.js';

function App() {
  const [currentPage, setCurrentPage] = useState('home');

  const navigate = (page) => {
    setCurrentPage(page);
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return <HomePage navigate={navigate} />;
      case 'about':
        return <AboutPage navigate={navigate} />;
      case 'game-modes':
        return <GameModePage navigate={navigate} />;
      case 'leaderboard':
        return <Leaderboard navigate={navigate} />;
      case 'login':
        return <LoginPage navigate={navigate} />;
      case 'news':
        return <NewsPage navigate={navigate} />;
      case 'register':
        return <RegisterPage navigate={navigate} />
      default:
        return <HomePage navigate={navigate} />;
    }
  };

  return (
    <div className="App">
      {renderPage()}
    </div>
  );
}

export default App;
