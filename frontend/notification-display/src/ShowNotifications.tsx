import React, { useState, useEffect } from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";

// interface EventData {
//   event: string;
//   data: {
//     message: string;
//   };
// }

const ShowNotifications: React.FC = () => {
  const WS_URL = "ws://localhost:8765/";
  const [showGif, setShowGif] = useState(false);
  const [message, setMessage] = useState("");
  const [countdown, setCountdown] = useState<number | null>(null);

  const { lastMessage, readyState } = useWebSocket(WS_URL, {
    share: false,
    shouldReconnect: () => true,
  });

  const replaceSingleQuotes = (str: string): string => {
    return str.replace(/'/g, '"');
  };
  useEffect(() => {
    if (readyState === ReadyState.OPEN) {
      console.log("WebSocket connection established");
    }
  }, [readyState]);

  useEffect(() => {
    const payload = lastMessage
      ? JSON.parse(replaceSingleQuotes(lastMessage.data))
      : null;
    console.log("Received message:", payload || "No message");
  }, [lastMessage]);

  useEffect(() => {
    if (countdown !== null) {
      if (countdown > 0) {
        const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
        return () => clearTimeout(timer);
      } else {
        setShowGif(false);
        setMessage("");
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
