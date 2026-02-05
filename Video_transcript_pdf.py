from moviepy import VideoFileClip
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
import os
from pathlib import Path
import shutil
import time
from config import API_KEY
from Word_Pdf_Converter import main_word_pdf_converter

def convert_video_to_audio(video_path, audio_path):
    """Convert video file to audio file"""
    try:
        # Load the video file
        video = VideoFileClip(video_path)
        # Extract the audio
        audio = video.audio
        # Save the audio as MP3
        audio.write_audiofile(audio_path)
        # Close the files to free up resources
        audio.close()
        video.close()
        print(f"Audio extracted successfully to {audio_path}")
        return True
    except Exception as e:
        print(f"Error converting video to audio: {e}")
        return False

def transcribe_audio_with_gemini(audio_path, api_key):
    try:
        import mimetypes
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel('gemini-2.0-flash')

        mime_type, _ = mimetypes.guess_type(audio_path)
        if mime_type is None:
            mime_type = "audio/mpeg"

        print("Uploading audio and generating transcript...")

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        # Enhanced prompt to request timestamps
        prompt = """Please transcribe this audio completely with timestamps. 
        
Format the transcript exactly as follows:
- Start each timestamped segment with the timestamp in MM:SS format (e.g., 0:05, 1:22, 10:45)
- Follow with the transcribed text for that segment
- Use natural breaks in speech to create segments (typically every 5-15 seconds)
- Ensure timestamps are accurate and sequential
- Make sure each segment is a complete thought or sentence

Example format:
0:05
First sentence of the transcript goes here.

0:15
Next sentence or segment continues here.

Please provide the complete timestamped transcript of the spoken content."""

        response = model.generate_content([
            {"mime_type": mime_type, "data": audio_bytes},
            {"text": prompt}
        ])

        print("Transcription completed successfully!")
        return response.text

    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None


def save_transcript_to_docx(transcript, video_name):
    try:
        output_dir = Path("video_transcript_pdf_output")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build a clean filename
        safe_name = video_name.replace(" ", "_")
        docx_path = output_dir / f"{safe_name}_transcript.docx"

        # Create Word document with better formatting
        doc = Document()
        
        # Add title with bold formatting
        title = doc.add_paragraph()
        title_run = title.add_run(f"{video_name}-Meeting Recording")
        title_run.bold = True
        title_run.font.size = Pt(14)
        
        # Add blank line
        doc.add_paragraph()
        
        # Add the transcript content
        # Split by lines and preserve formatting
        lines = transcript.split('\n')
        for line in lines:
            if line.strip():  # Only add non-empty lines
                doc.add_paragraph(line)
        
        doc.save(str(docx_path))

        print(f"Saved at (absolute): {docx_path.resolve()}")
        print(f"Exists? {docx_path.exists()}")
        
        # Force flush
        time.sleep(1)

        if not docx_path.exists():
            raise FileNotFoundError(f"File was not created: {docx_path}")

        print(f"Transcript saved to: {docx_path}")
        return docx_path

    except Exception as e:
        print(f"Error saving transcript to Word document: {e}")
        return None

def process_video_to_transcript(video_path, api_key, audio_format='mp3', clear_output_dir=True):
    """Complete pipeline: Video -> Audio -> Transcript -> Word Doc -> PDF"""
    try:
        # Create output directory (only clear on first video)
        output_dir = Path("video_transcript_pdf_output")
        if clear_output_dir and output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Extract video name (without extension)
        video_name = Path(video_path).stem
        # Generate audio file path
        audio_path = output_dir / f"{video_name}_audio.{audio_format}"

        print("Step 1: Converting video to audio...")
        if not convert_video_to_audio(video_path, str(audio_path)):
            raise Exception("Failed to convert video to audio")

        print("Step 2: Transcribing audio with Gemini API...")
        transcript = transcribe_audio_with_gemini(str(audio_path), api_key)
        if transcript is None:
            raise Exception("Failed to transcribe audio")

        print("Step 3: Saving transcript to Word document...")
        docx_path = save_transcript_to_docx(transcript, video_name)
        print(docx_path)
        if not docx_path:
            raise Exception("Failed to save transcript to Word document")

        print("\n✅ Process completed successfully!")
        print(f"📁 Audio file: {audio_path}")
        print(f"📄 Transcript document: {docx_path}")

        return str(docx_path)
    except Exception as e:
        print(f"Error in processing pipeline: {e}")
        return None

def convert_video_transcript_to_pdf(input_video_path, clear_output_dir=True):
    """Process video to transcript Word and PDF, saving all outputs in video_transcript_pdf_output directory"""
    # Process the video
    pdf_path = process_video_to_transcript(input_video_path, API_KEY, clear_output_dir=clear_output_dir)
    return pdf_path
