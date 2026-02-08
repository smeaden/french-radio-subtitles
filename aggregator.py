from pathlib import Path
import subprocess
import time
from datetime import datetime
import signal
import sys

# --- Configuration ---
ts_folder = Path("ts_segments")
chunks_folder = Path("chunks")
chunks_folder.mkdir(exist_ok=True)
sentinel_file = ts_folder / ".shutdown"

BATCH_SIZE = 15  # 15 x 4s = 60s
TIMEOUT_SECONDS = 120  # 2 minutes

processed = set()
shutdown_flag = False

def signal_handler(sig, frame):
    global shutdown_flag
    print('\n[INFO] Shutdown signal received, processing remaining files...')
    shutdown_flag = True

signal.signal(signal.SIGINT, signal_handler)

def get_unprocessed_files():
    """Get list of unprocessed .ts files, sorted by name"""
    all_files = sorted(ts_folder.glob("*.ts"))
    # Filter out temp files and already processed
    unprocessed = [f for f in all_files 
                   if f.name not in processed 
                   and "temp" not in f.name.lower() 
                   and "concat" not in f.name.lower()]
    return unprocessed

def get_newest_file_age(files):
    """Get age in seconds of the newest file"""
    if not files:
        return float('inf')
    newest_mtime = max(f.stat().st_mtime for f in files)
    return time.time() - newest_mtime

def concatenate_files(files, output_file):
    """Concatenate multiple TS files into one"""
    print(f"[INFO] Concatenating {len(files)} files -> {output_file.name}")
    
    # Create concat list file
    concat_list = chunks_folder / "concat_list.txt"
    with open(concat_list, 'w') as f:
        for ts_file in files:
            f.write(f"file '{ts_file.absolute()}'\n")
    
    # Run ffmpeg
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(output_file)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    concat_list.unlink()
    
    if result.returncode != 0:
        print(f"[ERROR] Concatenation failed: {result.stderr}")
        return False
    
    return True

def process_batch(files):
    """Process a batch of files into a chunk"""
    if not files:
        return
    
    # Generate chunk name based on first file in batch
    first_name = files[0].stem
    chunk_name = f"chunk_{first_name}.ts"
    chunk_file = chunks_folder / chunk_name
    
    # Concatenate
    if concatenate_files(files, chunk_file):
        # Mark all files as processed
        for f in files:
            processed.add(f.name)
        
        # Create metadata file
        metadata_file = chunks_folder / f"chunk_{first_name}.json"
        metadata = {
            'chunk_file': chunk_name,
            'source_files': [f.name for f in files],
            'created': datetime.now().isoformat()
        }
        
        import json
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"[INFO] Created chunk: {chunk_name} from {len(files)} segments")
    else:
        print(f"[ERROR] Failed to create chunk from batch")

def check_sentinel():
    """Check if downloader wrote a shutdown sentinel file"""
    if sentinel_file.exists():
        print("[INFO] Shutdown sentinel detected")
        sentinel_file.unlink()
        return True
    return False

# Main loop
print("[INFO] Aggregator starting (Ctrl+C to exit)")
print(f"[INFO] Batch size: {BATCH_SIZE} files (~60s)")
print(f"[INFO] Timeout: {TIMEOUT_SECONDS}s for incomplete batches")

while not shutdown_flag:
    try:
        unprocessed = get_unprocessed_files()
        
        if len(unprocessed) >= BATCH_SIZE:
            # Normal case: full batch available
            batch = unprocessed[:BATCH_SIZE]
            process_batch(batch)
        
        elif len(unprocessed) > 0:
            # Partial batch exists
            newest_age = get_newest_file_age(unprocessed)
            
            # Check if we should process partial batch
            sentinel_exists = check_sentinel()
            timeout_exceeded = newest_age > TIMEOUT_SECONDS
            
            if sentinel_exists or timeout_exceeded or shutdown_flag:
                reason = "shutdown" if (sentinel_exists or shutdown_flag) else f"timeout ({newest_age:.0f}s)"
                print(f"[INFO] Processing partial batch ({len(unprocessed)} files) due to {reason}")
                process_batch(unprocessed)
        
        # Check for shutdown signal
        if shutdown_flag:
            break
        
        time.sleep(2)
    
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        time.sleep(5)

# Process any remaining files on exit
print("[INFO] Final cleanup...")
unprocessed = get_unprocessed_files()
if unprocessed:
    print(f"[INFO] Processing {len(unprocessed)} remaining files")
    process_batch(unprocessed)

print("[INFO] Aggregator stopped")