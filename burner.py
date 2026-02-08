from pathlib import Path
import subprocess
import json

# --- Configuration ---
ts_folder = Path("ts_segments")
translated_folder = Path("translated")
output_folder = Path("videos_with_subs")
output_folder.mkdir(exist_ok=True)

def create_srt(text, duration_seconds, output_path, position='bottom'):
    """Create an SRT file with positioning tag"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("1\n")
        f.write("00:00:00,000 --> ")
        
        # Format duration as HH:MM:SS,mmm
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)
        milliseconds = int((duration_seconds % 1) * 1000)
        
        f.write(f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}\n")
        
        # Add alignment tag directly in subtitle text
        if position == 'top':
            f.write(f"{{\\an8}}{text}\n\n")  # an8 = top-center
        else:
            f.write(f"{{\\an2}}{text}\n\n")  # an2 = bottom-center

def get_duration(ts_file):
    """Get duration of TS file using ffprobe"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(ts_file)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 4.0

# Process each JSON file
for json_file in sorted(translated_folder.glob("*.json")):
    base_name = json_file.stem
    ts_file = ts_folder / f"{base_name}.ts"
    
    if not ts_file.exists():
        print(f"[WARN] TS file not found for {json_file.name}, skipping")
        continue
    
    # Load translation data
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    french_text = data.get("french", "")
    english_text = data.get("english", "")
    
    if not french_text or not english_text:
        print(f"[WARN] Missing text in {json_file.name}, skipping")
        continue
    
    # Get duration
    duration = get_duration(ts_file)
    
    # Create SRT files with inline positioning
    french_srt = output_folder / f"{base_name}_fr.srt"
    english_srt = output_folder / f"{base_name}_en.srt"
    
    create_srt(french_text, duration, french_srt, position='top')
    create_srt(english_text, duration, english_srt, position='bottom')
    
    # Output MP4 file
    output_file = output_folder / f"{base_name}.mp4"
    
    # Fix path for Windows
    french_srt_escaped = str(french_srt).replace('\\', '/').replace(':', '\\:')
    english_srt_escaped = str(english_srt).replace('\\', '/').replace(':', '\\:')
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=black:s=1280x720:d={duration}",
        "-i", str(ts_file),
        "-filter_complex",
        (
            # French at TOP
            "[0:v]subtitles=" + french_srt_escaped + ":force_style='"
            "FontName=Arial,FontSize=18,PrimaryColour=&H00FFFF,OutlineColour=&H000000,"
            "BorderStyle=1,Outline=2,Shadow=1,MarginV=30,Bold=1'"
            "[v1];"
            # English at BOTTOM
            "[v1]subtitles=" + english_srt_escaped + ":force_style='"
            "FontName=Arial,FontSize=18,PrimaryColour=&H00FF00,OutlineColour=&H000000,"
            "BorderStyle=1,Outline=2,Shadow=1,MarginV=30,Bold=1'"
            "[vout]"
        ),
        "-map", "[vout]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "copy",
        "-shortest",
        str(output_file)
    ]
    
    print(f"[INFO] Processing {ts_file.name} -> {output_file.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"[ERROR] FFmpeg failed:")
        print(result.stderr)
    else:
        print(f"[INFO] Created {output_file.name}")
        french_srt.unlink()
        english_srt.unlink()