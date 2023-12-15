from flask import Flask, Response
from playsound import playsound
from dotenv import load_dotenv
import time
import os
import base64

load_dotenv()
GIF_PATH = os.environ.get("PATH_TO_GIF") or ""
SOUND_FILE = os.environ.get("NOTIFICATION_SOUND_FILE_PATH")

donation_trigger = False

app = Flask(__name__)

# Function to generate a simple GIF image


def generate_gif():
    return open(GIF_PATH, 'rb').read()

# Route to serve the HTML page with embedded JavaScript


@app.route('/')
def index():
    return """
    <html>
    <head>
        <script>
            const sleep = (delay) => new Promise((resolve) => setTimeout(resolve, delay));
            const eventSource = new EventSource('/events');

            eventSource.onmessage = async function(event) {
                const gifUrl = event.data; // URL of the updated GIF image
                // Update the image on your webpage
                var img = document.getElementById('gifImage');
                img.style.visibility = 'hidden';
                img.src = gifUrl;
                img.style.visibility = 'visible';
                await sleep(10000);
                img.style.visibility = 'hidden';
            };
        </script>
    </head>
    <body>
        <img id="gifImage" src="" alt="GIF Image" style = 'visibility: hidden'>
    </body>
    </html>
    """


@app.route("/donation", methods=['POST'])
def donation_received():
    global donation_trigger
    donation_trigger = True
    return Response(status=200)

# SSE route triggered on a server event


@app.route('/events')
def events():
    def generate():
        global donation_trigger
        while True:
            if donation_trigger:
                gif_data = generate_gif()
                encoded_gif = base64.b64encode(gif_data).decode('utf-8')
                yield f"data: data:image/gif;base64,{encoded_gif}\n\n"
                donation_trigger = False
                if SOUND_FILE:
                    playsound(SOUND_FILE)  # Play notification sound

            time.sleep(1)

    return Response(generate(), content_type='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True)
