from flask import Flask, request, send_file, render_template, jsonify
import asyncio
import edge_tts
import io
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[]
)

CHUNK_WORD_LIMIT = 400

def split_into_chunks(text, limit=CHUNK_WORD_LIMIT):
    words = text.split()
    chunks = []
    for i in range(0, len(words), limit):
        chunks.append(' '.join(words[i:i+limit]))
    return chunks if chunks else ['']

print("Loading voice list...")
VOICES_CACHE = asyncio.run(edge_tts.list_voices())
print(f"Loaded {len(VOICES_CACHE)} voices.")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/privacy-policy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/api/voices')
def get_voices():
    return jsonify(VOICES_CACHE)

@app.route('/test-voice')
@limiter.limit("10 per minute")
def test_voice():
    text = request.args.get('text', 'Hello from my own server')
    voice = request.args.get('voice', 'en-US-AriaNeural')
    mode = request.args.get('mode', 'download')
    rate = request.args.get('rate', '+0%')
    pitch = request.args.get('pitch', '+0Hz')

    chunks = split_into_chunks(text)

    async def generate_all():
        buffer = io.BytesIO()
        for chunk_text in chunks:
            communicate = edge_tts.Communicate(chunk_text, voice, rate=rate, pitch=pitch)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])
        buffer.seek(0)
        return buffer

    audio_buffer = asyncio.run(generate_all())

    return send_file(
        audio_buffer,
        mimetype="audio/mpeg",
        as_attachment=(mode != 'preview'),
        download_name="voice.mp3"
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)