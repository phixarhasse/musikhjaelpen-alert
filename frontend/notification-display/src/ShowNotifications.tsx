import React, { useState, useEffect } from 'react';

interface EventData {
  event: string;
  data: {
    message: string;
  }
}

const ShowNotifications: React.FC = () => {
  const [showGif, setShowGif] = useState(false);
  const [message, setMessage] = useState('');
  const [countdown, setCountdown] = useState<number | null>(null);

  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8765/');

    socket.onopen = () => {
      console.log('WebSocket connection established');
    };

    socket.onmessage = (event) => {
      const payload: EventData = JSON.parse(event.data);
      switch (payload.event) {
        case 'donation':
          setShowGif(true);
          setMessage(payload.data.message);
          setTimeout(() => {
            setShowGif(false);
            setMessage('');
          }, 5000); // Hide GIF and clear message after 5 seconds
          break;
        case 'turbo_donation':
          setShowGif(true);
          setMessage(payload.data.message);
          setCountdown(30); // Start 30-second countdown
          setTimeout(() => {
            setShowGif(false);
            setMessage('');
          }, 5000); // Hide GIF and clear message after 5 seconds
          break;
        default:
          console.log('Unknown event type:', payload.event);
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    socket.onclose = () => {
      console.log('WebSocket connection closed');
    };

    return () => {
      socket.close();
    };
  }, []);

  useEffect(() => {
    if (countdown !== null) {
      if (countdown > 0) {
        const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
        return () => clearTimeout(timer);
      } else {
        setShowGif(false);
        setMessage('');
        setCountdown(null);
      }
    }
  }, [countdown]);

  return (
    <div>
      {showGif && (
        <div>
          <img src="path-to-your-gif.gif" alt="Triggered Event" />
          <p>{message}</p>
        </div>
      )}
      {countdown !== null && <p>Countdown: {countdown} seconds</p>}
    </div>
  );
};

export default ShowNotifications;