import whisper
from transformers import MarianMTModel, MarianTokenizer
from pathlib import Path
import json
import time

# --- Configuration ---
chunks_folder = Path("chunks")
output_folder = Path("translated")
output_folder.mkdir(exist_ok=True)

whisper_model_name = "small"
translation_model_name = "Helsinki-NLP/opus-mt-fr-en"

# Load models
print("[INFO] Loading Whisper model...")
whisper_model = whisper.load_model(whisper_model_name)
print("[INFO] Loading translation model...")
tokenizer = MarianTokenizer.from_pretrained(translation_model_name)
translation_model = MarianMTModel.from_pretrained(translation_model_name)

def translate_french(text):
    if not text.strip():
        return ""
    inputs = tokenizer(text, return_tensors="pt", padding=True)
    translated = translation_model.generate(**inputs)
    return tokenizer.decode(translated[0], skip_special_tokens=True)

def split_text_by_time(segments, source_files):
    """
    Split Whisper segments back into original ~4-second chunks
    Returns dict mapping source_file -> {french, english, start, end}
    """
    # Calculate duration per source file (approximately 4s each)
    file_duration = 4.0
    result = {}
    
    for i, source_file in enumerate(source_files):
        chunk_start = i * file_duration
        chunk_end = (i + 1) * file_duration
        
        # Find all segments that overlap with this time window
        texts_fr = []
        
        for seg in segments:
            seg_start = seg['start']
            seg_end = seg['end']
            
            # Check if segment overlaps with this chunk
            if seg_start < chunk_end and seg_end > chunk_start:
                texts_fr.append(seg['text'])
        
        french_text = ' '.join(texts_fr).strip()
        english_text = translate_french(french_text) if french_text else ""
        
        result[source_file] = {
            'french': french_text,
            'english': english_text,
            'start': chunk_start,
            'end': chunk_end
        }
    
    return result

# Main loop
processed = set()
print("[INFO] Watching chunks folder for aggregated files...")

while True:
    chunk_files = sorted(chunks_folder.glob("chunk_*.ts"))
    
    for chunk_file in chunk_files:
        if chunk_file.name in processed:
            continue
        
        # Load metadata to get source files
        metadata_file = chunks_folder / f"{chunk_file.stem}.json"
        if not metadata_file.exists():
            print(f"[WARN] No metadata for {chunk_file.name}, skipping")
            continue
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        source_files = metadata['source_files']
        
        print(f"[INFO] Transcribing {chunk_file.name} ({len(source_files)} segments)...")
        
        # Transcribe entire chunk with word-level timestamps
        result = whisper_model.transcribe(
            str(chunk_file),
            language='fr',
            word_timestamps=False  # Use segment-level timestamps for now
        )
        
        # Split back into 4-second segments
        segment_data = split_text_by_time(result['segments'], source_files)
        
        # Save individual JSON files for each source segment
        for source_file, data in segment_data.items():
            base_name = Path(source_file).stem
            json_file = output_folder / f"{base_name}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'ts_file': source_file,
                    'french': data['french'],
                    'english': data['english'],
                    'start': data['start'],
                    'end': data['end'],
                    'chunk_source': chunk_file.name
                }, f, ensure_ascii=False, indent=2)
            
            print(f"[INFO] Created {json_file.name}")
        
        processed.add(chunk_file.name)
        print(f"[INFO] Completed {chunk_file.name}")
    
    time.sleep(5)