import os
import uuid
from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import imageio_ffmpeg

app = Flask(__name__)

# Temporary download directory
DOWNLOAD_DIR = os.path.join(os.getcwd(), "web_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    data = request.json
    url = data.get("url", "").strip()
    file_type = data.get("type", "video") # "video" or "audio"

    if not url:
        return jsonify({"success": False, "error": "กรุณากรอกลิงก์วิดีโอ"}), 400

    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        unique_id = str(uuid.uuid4())[:8]
        
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, f'%(title)s_{unique_id}.%(ext)s'),
            'ffmpeg_location': ffmpeg_exe,
            'noplaylist': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        }

        if file_type == 'audio':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            ydl_opts.update({
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if file_type == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'

            if not os.path.exists(filename):
                # Fallback search in download dir with unique_id
                for f in os.listdir(DOWNLOAD_DIR):
                    if unique_id in f:
                        filename = os.path.join(DOWNLOAD_DIR, f)
                        break

            basename = os.path.basename(filename)
            return jsonify({
                "success": True, 
                "filename": basename,
                "download_url": f"/get-file/{basename}"
            })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/get-file/<path:filename>")
def get_file(filename):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "ไม่พบไฟล์หรือไฟล์ถูกลบไปแล้ว", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
