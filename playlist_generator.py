from pathlib import Path
import time
from datetime import datetime
import json

# --- Configuration ---
output_folder = Path("videos_with_subs")
playlist_folder = Path("playlist")
playlist_folder.mkdir(exist_ok=True)

playlist_file = playlist_folder / "segments.json"
rewind_hours = 6
delete_after_hours = 24

def generate_playlist():
    """Generate simple JSON list of available segments"""
    now = time.time()
    rewind_cutoff = now - (rewind_hours * 3600)
    delete_cutoff = now - (delete_after_hours * 3600)
    
    segments = []
    deleted = 0
    
    for mp4_file in sorted(output_folder.glob("*.mp4")):
        # Skip temporary files
        if "temp" in mp4_file.name.lower() or "concat" in mp4_file.name.lower():
            continue
        
        mtime = mp4_file.stat().st_mtime
        age_hours = (now - mtime) / 3600
        
        # Delete old segments
        if mtime < delete_cutoff:
            print(f"[INFO] Deleting old segment: {mp4_file.name} (age: {age_hours:.1f}h)")
            try:
                mp4_file.unlink()
                deleted += 1
            except Exception as e:
                print(f"[WARN] Could not delete {mp4_file.name}: {e}")
            continue
        
        # Include segments within rewind window
        if mtime >= rewind_cutoff:
            segments.append({
                'file': mp4_file.name,
                'basename': mp4_file.stem,
                'timestamp': mtime
            })
    
    if not segments:
        print("[WARN] No segments available")
        return 0
    
    # Save playlist
    playlist_data = {
        'updated': datetime.now().isoformat(),
        'total_segments': len(segments),
        'segments': segments
    }
    
    with open(playlist_file, 'w') as f:
        json.dump(playlist_data, f, indent=2)
    
    print(f"[INFO] {datetime.now().strftime('%H:%M:%S')} - Playlist: {len(segments)} segments (deleted: {deleted})")
    return len(segments)

# Main
print("[INFO] Simple playlist generator starting (Ctrl+C to exit)")
print(f"[INFO] Rewind: {rewind_hours}h, Delete after: {delete_after_hours}h")

while True:
    try:
        generate_playlist()
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")
        break
    except Exception as e:
        print(f"[ERROR] {e}")
    
    time.sleep(10)