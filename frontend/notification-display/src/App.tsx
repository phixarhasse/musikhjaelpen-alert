// src/App.tsx
import React from 'react';
import './App.css';
import EventDrivenComponent from './ShowNotifications';

const App: React.FC = () => {
  return (
    <div className="App">
      <header className="App-header">
        <EventDrivenComponent />
      </header>
    </div>
  );
};

export default App;