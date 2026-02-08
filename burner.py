from pathlib import Path
import subprocess
import json

# --- Configuration ---
chunks_folder = Path("chunks")
translated_folder = Path("translated")
output_folder = Path("videos_with_subs")
output_folder.mkdir(exist_ok=True)

# --- Font Configuration ---
FONT_SIZE = 18
FONT_NAME = "Arial"
FONT_OUTLINE = 2
FONT_SHADOW = 1
MARGIN_V = 30
FRENCH_COLOR = "&H00FFFF"  # Cyan
ENGLISH_COLOR = "&H00FF00"  # Yellow/Green
OUTLINE_COLOR = "&H000000"  # Black

def create_multi_cue_srt(segments_data, duration, output_path, language='french'):
    """Create an SRT file with multiple timed cues"""
    with open(output_path, "w", encoding="utf-8") as f:
        cue_number = 1
        
        for i, (source_file, data) in enumerate(segments_data.items()):
            start_time = data['start']
            end_time = data['end']
            
            # Get the appropriate text
            text = data['french'] if language == 'french' else data['english']
            
            if not text.strip():
                continue
            
            # Format times as HH:MM:SS,mmm
            def format_time(seconds):
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                millis = int((seconds % 1) * 1000)
                return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
            
            f.write(f"{cue_number}\n")
            f.write(f"{format_time(start_time)} --> {format_time(end_time)}\n")
            
            # Add positioning tag
            if language == 'french':
                f.write(f"{{\\an8}}{text}\n\n")  # Top
            else:
                f.write(f"{{\\an2}}{text}\n\n")  # Bottom
            
            cue_number += 1

def get_duration(chunk_file):
    """Get duration using ffprobe"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(chunk_file)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 60.0

# Process each chunk
processed = set()

print("[INFO] Burner watching for chunks to process...")

import time
while True:
    chunk_files = sorted(chunks_folder.glob("chunk_*.ts"))
    
    for chunk_file in chunk_files:
        if chunk_file.name in processed:
            continue
        
        # Load metadata
        metadata_file = chunks_folder / f"{chunk_file.stem}.json"
        if not metadata_file.exists():
            print(f"[WARN] No metadata for {chunk_file.name}, skipping")
            continue
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        source_files = metadata['source_files']
        
        # Check if all translation JSONs exist
        segments_data = {}
        all_translations_ready = True
        
        for source_file in source_files:
            base_name = Path(source_file).stem
            json_file = translated_folder / f"{base_name}.json"
            
            if not json_file.exists():
                all_translations_ready = False
                break
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                segments_data[source_file] = data
        
        if not all_translations_ready:
            continue
        
        print(f"[INFO] Processing {chunk_file.name} with {len(segments_data)} segments...")
        
        # Get duration
        duration = get_duration(chunk_file)
        
        # Create SRT files with multiple cues
        french_srt = output_folder / f"{chunk_file.stem}_fr.srt"
        english_srt = output_folder / f"{chunk_file.stem}_en.srt"
        
        create_multi_cue_srt(segments_data, duration, french_srt, 'french')
        create_multi_cue_srt(segments_data, duration, english_srt, 'english')
        
        # Output MP4 file
        output_file = output_folder / f"{chunk_file.stem}.mp4"
        
        # Fix paths for Windows
        french_srt_escaped = str(french_srt).replace('\\', '/').replace(':', '\\:')
        english_srt_escaped = str(english_srt).replace('\\', '/').replace(':', '\\:')
        
        # Build font style strings using constants
        french_style = (
            f"FontName={FONT_NAME},FontSize={FONT_SIZE},PrimaryColour={FRENCH_COLOR},"
            f"OutlineColour={OUTLINE_COLOR},BorderStyle=1,Outline={FONT_OUTLINE},"
            f"Shadow={FONT_SHADOW},MarginV={MARGIN_V},Bold=1"
        )
        
        english_style = (
            f"FontName={FONT_NAME},FontSize={FONT_SIZE},PrimaryColour={ENGLISH_COLOR},"
            f"OutlineColour={OUTLINE_COLOR},BorderStyle=1,Outline={FONT_OUTLINE},"
            f"Shadow={FONT_SHADOW},MarginV={MARGIN_V},Bold=1"
        )
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=black:s=1280x720:d={duration}",
            "-i", str(chunk_file),
            "-filter_complex",
            (
                # French at TOP
                f"[0:v]subtitles={french_srt_escaped}:force_style='{french_style}'[v1];"
                # English at BOTTOM
                f"[v1]subtitles={english_srt_escaped}:force_style='{english_style}'[vout]"
            ),
            "-map", "[vout]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-g", "30",              # Keyframe every 30 frames (1 second at 30fps)
            "-keyint_min", "30",     # Minimum keyframe interval
            "-sc_threshold", "0",    # Disable scene change detection for regular keyframes
            "-c:a", "copy",
            "-shortest",
            str(output_file)
        ]
        
        print(f"[INFO] Creating video {output_file.name}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"[ERROR] FFmpeg failed:")
            print(result.stderr)
        else:
            print(f"[INFO] Created {output_file.name}")
            # Clean up temporary SRT files
            french_srt.unlink()
            english_srt.unlink()
            processed.add(chunk_file.name)
    
    time.sleep(5)