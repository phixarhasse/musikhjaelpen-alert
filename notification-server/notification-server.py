from flask import Flask, request, jsonify, redirect, url_for, Response
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

@app.route('/')
def index():
    show_timer = request.args.get('show_timer', 'false').lower() == 'true'
    return generate_html(show_timer)

@app.route("/donation", methods=['POST'])
def donation():
    global donation_trigger
    donation_trigger = True
    return jsonify({"message": "Donation received"}), 200

@app.route("/donation-200", methods=['POST'])
def donation_200():
    global donation_trigger
    donation_trigger = True
    # Mimic the functionality of the existing donation route
    return redirect(url_for('index', show_timer='true'))

def generate_html(show_timer):
    countdown_script = """
        <script>
            function startCountdown(duration, display) {
                var timer = duration, minutes, seconds;
                setInterval(function () {
                    minutes = parseInt(timer / 60, 10);
                    seconds = parseInt(timer % 60, 10);

                    minutes = minutes < 10 ? "0" + minutes : minutes;
                    seconds = seconds < 10 ? "0" + seconds : seconds;

                    display.textContent = minutes + ":" + seconds;

                    if (--timer < 0) {
                        timer = duration;
                    }
                }, 1000);
            }

            window.onload = function () {
                var countdownDuration = 30; // 30 seconds
                var display = document.querySelector('#countdown');
                startCountdown(countdownDuration, display);
            };
        </script>
    """ if show_timer else ""

    return f"""
    <html>
    <head>
        <script>
            const sleep = (delay) => new Promise((resolve) => setTimeout(resolve, delay));
            const eventSource = new EventSource('/events');

            eventSource.onmessage = async function(event) {{
                const gifUrl = event.data; // URL of the updated GIF image
                // Update the image on your webpage
                var img = document.getElementById('gifImage');
                img.style.visibility = 'hidden';
                img.src = gifUrl;
                img.style.visibility = 'visible';
                await sleep(10000);
                img.style.visibility = 'hidden';
            }};
        </script>
        {countdown_script}
    </head>
    <body>
        <img id="gifImage" src="" alt="GIF Image" style='visibility: hidden'>
        {"<div>Countdown: <span font-size: 5rem; style='color:red' id='countdown'>00:30</span></div>" if show_timer else ""}
    </body>
    </html>
    """

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

if __name__ == "__main__":
    app.run(debug=True)
