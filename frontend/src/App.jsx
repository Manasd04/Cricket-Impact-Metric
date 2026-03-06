import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './index.css';

import Home from './pages/Home';
import PlayerDashboard from './pages/PlayerDashboard';
import Leaderboard from './pages/Leaderboard';

function App() {
  return (
    <Router>
      <div className="app-container" style={{ display: 'block' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/player/:playerName" element={<PlayerDashboard />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
