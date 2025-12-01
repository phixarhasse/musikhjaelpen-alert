#!/usr/bin/env python3
"""
ws_to_twitch.py

Listen to a websocket server and forward received messages to Twitch chat via IRC.

Configuration (environment variables or CLI args):
- TWITCH_NICK: Twitch username (required)
- TWITCH_OAUTH: OAuth token/password (required). Format: "oauth:xxxxxxxx" or just the token; the script will add prefix if needed.
- TWITCH_CHANNEL: Channel name to join (required, without #)
- WS_URI: WebSocket URI (default: ws://localhost:8765)

Usage example:
  TWITCH_NICK=myuser TWITCH_OAUTH=oauth:xxxx TWITCH_CHANNEL=mychannel python ws_to_twitch.py

This script is minimal and includes simple reconnect/backoff logic.
"""

import asyncio
import os
import argparse
import logging
import sys
import ssl

import websockets
from dotenv import load_dotenv

IRC_HOST = "irc.chat.twitch.tv"
IRC_PORT = 6667

load_dotenv()

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")


async def connect_twitch(nick: str, token: str, channel: str, tls: bool = False, port: int | None = None):
    """Establish an IRC connection to Twitch and join the channel. Returns (reader, writer)."""
    backoff = 1
    while True:
        try:
            use_port = port if port is not None else (6697 if tls else IRC_PORT)
            logging.info("Connecting to Twitch IRC %s:%s (tls=%s)", IRC_HOST, use_port, tls)

            if tls:
                ssl_ctx = ssl.create_default_context()
                reader, writer = await asyncio.open_connection(IRC_HOST, use_port, ssl=ssl_ctx, server_hostname=IRC_HOST)
            else:
                reader, writer = await asyncio.open_connection(IRC_HOST, use_port)
            # Ensure token has oauth: prefix
            if not token.startswith("oauth:"):
                token_to_use = f"oauth:{token}"
            else:
                token_to_use = token

            writer.write(f"PASS {token_to_use}\r\n".encode())
            writer.write(f"NICK {nick}\r\n".encode())
            writer.write(f"JOIN #{channel}\r\n".encode())
            await writer.drain()

            # Start a reader task to capture server messages and respond to PINGs
            read_task = asyncio.create_task(irc_reader(reader, writer))

            logging.info("Joined Twitch channel #%s as %s", channel, nick)
            return reader, writer, read_task
        except Exception:
            logging.exception("Failed connecting to Twitch IRC, retrying in %s seconds", backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)


async def send_privmsg(writer: asyncio.StreamWriter, channel: str, message: str):
    """Send a PRIVMSG to the Twitch channel. Keeps a small delay to be polite."""
    try:
        # Twitch IRC requires messages to be CRLF-terminated
        payload = f"PRIVMSG #{channel} :{message}\r\n"
        writer.write(payload.encode())
        await writer.drain()
        logging.info("Sent to Twitch #%s: %s", channel, message)
        # Small sleep to avoid bursting messages
        await asyncio.sleep(0.5)
    except Exception:
        logging.exception("Error sending message to Twitch")
        raise


async def irc_reader(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Background task: read IRC server messages and handle PING/PONG."""
    try:
        while True:
            line = await reader.readline()
            if not line:
                logging.warning("IRC connection closed by server")
                break
            text = line.decode(errors="ignore").rstrip()
            logging.info("IRC <- %s", text)
            # Respond to PINGs
            if text.startswith("PING"):
                # Format: PING :tmi.twitch.tv
                parts = text.split(" ", 1)
                param = parts[1] if len(parts) > 1 else ""
                pong = f"PONG {param}\r\n"
                try:
                    writer.write(pong.encode())
                    await writer.drain()
                    logging.info("IRC -> %s", pong.strip())
                except Exception:
                    logging.exception("Failed to send PONG")
                    break
    except asyncio.CancelledError:
        logging.info("IRC reader task cancelled")
    except Exception:
        logging.exception("Error in IRC reader")


async def ws_listener(ws_uri: str, nick: str, token: str, channel: str, tls: bool = False, port: int | None = None):
    twitch_reader = None
    twitch_writer = None
    twitch_read_task = None

    # Outer loop handles reconnects for both WS and Twitch IRC
    while True:
        try:
            if twitch_writer is None:
                twitch_reader, twitch_writer, twitch_read_task = await connect_twitch(nick, token, channel, tls=tls, port=port)

            logging.info("Connecting to websocket %s", ws_uri)
            async with websockets.connect(ws_uri, ping_timeout=None) as ws:
                logging.info("Connected to websocket server")
                async for message in ws:
                    logging.info("Received WS message: %s", message)
                    try:
                        # Forward the actual message received from websocket
                        await send_privmsg(twitch_writer, channel, message)
                    except Exception:
                        # If send fails, drop twitch_writer so it will reconnect
                        try:
                            twitch_writer.close()
                        except Exception:
                            pass
                        twitch_writer = None
                        if twitch_read_task:
                            twitch_read_task.cancel()
                            twitch_read_task = None
                        break

        except websockets.exceptions.ConnectionClosed as e:
            logging.warning("WebSocket connection closed: %s", e)
        except Exception:
            logging.exception("Unexpected error in main loop")

        logging.info("Reconnecting in 3 seconds...")
        await asyncio.sleep(3)


def parse_args():
    p = argparse.ArgumentParser(description="Forward websocket messages to Twitch chat")
    p.add_argument("--ws-uri", default=os.environ.get("WS_URI", "ws://localhost:8765"), help="WebSocket URI (or set WS_URI)")
    p.add_argument("--nick", default=os.environ.get("TWITCH_NICK"), help="Twitch nick (or set TWITCH_NICK)")
    p.add_argument("--token", default=os.environ.get("TWITCH_OAUTH"), help="Twitch OAuth token/password (or set TWITCH_OAUTH)")
    p.add_argument("--channel", default=os.environ.get("TWITCH_CHANNEL"), help="Twitch channel (or set TWITCH_CHANNEL)")
    # TLS: connect to port 6697 with SSL when enabled
    env_tls = os.environ.get("TWITCH_TLS")
    default_tls = False
    if env_tls and env_tls.lower() in ("1", "true", "yes", "on"):
        default_tls = True
    p.add_argument("--tls", action="store_true", default=default_tls, help="Enable TLS for Twitch IRC (uses port 6697). Can also set TWITCH_TLS=1 in .env")
    p.add_argument("--port", type=int, default=(6697 if default_tls else IRC_PORT), help="Port to connect to Twitch IRC (default 6697 for TLS, 6667 otherwise)")
    return p.parse_args()


def main():
    args = parse_args()
    if not args.nick or not args.token or not args.channel:
        print("Missing required Twitch settings. Provide via env (TWITCH_NICK, TWITCH_OAUTH, TWITCH_CHANNEL) or CLI args.")
        sys.exit(2)

    try:
        asyncio.run(ws_listener(args.ws_uri, args.nick, args.token, args.channel, tls=args.tls, port=args.port))
    except KeyboardInterrupt:
        logging.info("Interrupted by user, exiting")


if __name__ == "__main__":
    main()
