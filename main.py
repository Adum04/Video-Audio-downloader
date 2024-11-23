import os
from datetime import timedelta
from flask import (
    Flask,
    render_template,
    send_from_directory,
    session,
    redirect,
    url_for,
)
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired
import yt_dlp

app = Flask(__name__)
app.config["SECRET_KEY"] = "Adum1234567890"  # Replace with a strong secret key
app.config["UPLOAD_FOLDER"] = "downloads"  # Store downloads within your app
app.permanent_session_lifetime = timedelta(seconds=29)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)  # Create downloads folder


class Myform(FlaskForm):
    link = StringField("Link", validators=[DataRequired()])
    download_video = SubmitField("Download Video")  # Button for video
    download_audio = SubmitField("Download Audio")


@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
def home():
    form = Myform()
    download_filename = None
    download_type = None  # Track the type (audio or video)

    # Check if a filename exists in the session
    if "download_filename" in session:
        download_filename = session["download_filename"]
        download_type = session["download_type"]

    session.permanent = True

    if form.validate_on_submit():
        url = form.link.data
        try:
            if form.download_video.data:  # If video download button is clicked
                download_filename = download_video(url)
                download_type = "video"
            elif form.download_audio.data:  # If audio download button is clicked
                download_filename = download_audio(url)
                download_type = "audio"

            # Store filename and type in session
            session["download_filename"] = download_filename
            session["download_type"] = download_type
        except Exception as e:
            return f"Error has occurred: {e}"

        return render_template(
            "home.html",
            form=form,
            download_filename=download_filename,
            download_type=download_type,
        )

    return render_template(
        "home.html",
        form=form,
        download_filename=download_filename,
        download_type=download_type,
    )


def download_audio(url):
    ydl_opts = {
        "format": "bestaudio/best",  # Download best audio quality
        "outtmpl": os.path.join(
            app.config["UPLOAD_FOLDER"], "%(title)s.%(ext)s"
        ),  # Correct output path
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "postprocessor_args": ["-ar", "44100"],
        "ffmpeg_location": "/opt/homebrew/bin/ffmpeg",  # Path to FFmpeg
        "noplaylist": True,  # Only process a single video
        "verbose": True,  # Enable verbose logging for debugging
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=True)  # Extract and download
            downloaded_file = ydl.prepare_filename(info_dict)  # Get resolved filename
            print(f"Resolved file path: {downloaded_file}")

            # Ensure file extension is updated to .mp3 after postprocessing
            downloaded_file = downloaded_file.replace(".webm", ".mp3").replace(
                ".m4a", ".mp3"
            )
            return os.path.basename(downloaded_file)  # Return filename only
        except Exception as e:
            print(f"Error during download: {e}")
            raise e


def download_video(url):
    # Generate a consistent and valid filename
    filename = f"{url.split('/')[-1].split('?')[0]}.mp4"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": filepath,  # Ensure the full path includes desired filename
        "merge_output_format": "mp4",  # Force output format to MP4
        "cookies": "cookies.txt",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            print(f"Download completed: {filename}")
            return filename
        except Exception as e:
            print(f"An error occurred: {e}")
            raise e


@app.route("/download/<filename>", methods=["GET"])
def download_page(filename):
    return render_template("download.html", filename=filename)


@app.route("/downloads/<path:filename>", methods=["GET"])
def download_file(filename):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"], filename, as_attachment=True
    )


@app.route("/clear_session", methods=["GET"])
def clear_session():
    session.pop("download_filename", None)
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run()
