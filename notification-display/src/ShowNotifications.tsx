import React, { useState, useEffect } from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";
import cycling from "./assets/gifs/cycling.gif";
import sprint from "./assets/gifs/sprint.gif";
import g1 from "./assets/gifs/thegrinch/g1.gif";
import g2 from "./assets/gifs/thegrinch/g2.gif";
import g3 from "./assets/gifs/thegrinch/g3.gif";
import MessageText from "./components/MessageText";
import CountdownText from "./components/CountdownText";

interface EventData {
  event: string;
  message: string;
}

// TODO: Implement a queue so refresh time can be faster than notification rate

const ShowNotifications: React.FC = () => {
  const WS_URL = "ws://localhost:8765/";
  const [showGif, setShowGif] = useState(false);
  const [selectedGif, setSelectedGif] = useState("");
  const [message, setMessage] = useState("");
  const [countdown, setCountdown] = useState<number | null>(null);

  const { lastMessage, readyState } = useWebSocket(WS_URL, {
    share: false,
    shouldReconnect: () => true,
  });

  const cycleSelectedGrinchGif = () => {
    switch (selectedGif) {
      case g1:
        setSelectedGif(g2);
        break;
      case g2:
        setSelectedGif(g3);
        break;
      case g3:
        setSelectedGif(g1);
        break;
      default:
        setSelectedGif(g1);
        break;
    }
  };

  const showGifFor10Seconds = () => {
    setShowGif(true);
    setTimeout(() => {
      setShowGif(false);
    }, 10500);
  };

  const showMessageFor10Seconds = (message: string) => {
    setMessage(message);
    setTimeout(() => {
      setMessage("");
    }, 10000);
  };

  const showGifAndMessageFor10Seconds = (message: string) => {
    setShowGif(true);
    setMessage(message);
    setCountdown(10);
    setTimeout(() => {
      setShowGif(false);
      setMessage("");
    }, 10000);
  };

  const replaceSingleQuotes = (str: string): string => {
    return str.replace(/'/g, '"');
  };

  useEffect(() => {
    if (readyState === ReadyState.OPEN) {
      console.log("WebSocket connection established");
    }
  }, [readyState]);

  useEffect(() => {
    const payload: EventData | null = lastMessage
      ? JSON.parse(replaceSingleQuotes(lastMessage.data))
      : null;

    if (payload && payload?.event) {
      switch (payload.event) {
        case "donation":
          showGifAndMessageFor10Seconds(payload.message);
          // showMessageFor10Seconds(payload.message);
          break;
        case "sprint_donation":
          setSelectedGif(sprint);
          setCountdown(10);
          showGifFor10Seconds();
          showMessageFor10Seconds(payload.message);
          break;
        default:
          console.log("Unknown event type");
      }
    }
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
          <img src={selectedGif} alt="Event gif" />
          <MessageText message={message} />
        </div>
      )}
      {countdown !== null && <CountdownText count={countdown} />}
    </div>
  );
};

export default ShowNotifications;
