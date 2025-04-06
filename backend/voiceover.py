import os
from dotenv import load_dotenv
import hashlib
import queue
from typing import List, Dict, Any
from pydub import AudioSegment
from tqdm.auto import tqdm
import httpx
import backoff
import asyncio
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

ELEVEN_LABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVEN_LABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# Create audio directory if it doesn't exist
AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio")
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)
    logger.info(f"Created audio directory: {AUDIO_DIR}")

# Voice IDs mapping
VOICE_IDS = {
    "Jessica": "21m00Tcm4TlvDq8ikWAM",  # Female, soft and caring voice
    "Michael": "8iDUAV5slUpRv30f3cyz",  # Male, American, Casual
    "David": "8iDUAV5slUpRv30f3cyz",    # Male, American, Friendly
    "Emily": "21m00Tcm4TlvDq8ikWAM",    # Female, American, Expressive
}

def get_clip_filename(speaker: str, text: str, output_dir: str):
    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    filename = os.path.join(output_dir, f"{speaker}_{text_hash}.mp3")
    logger.debug(f"Generated filename for {speaker}: {filename}")
    return filename

async def generate_voice_clips(dialogue: List[Dict[str, Any]], output_dir: str = AUDIO_DIR):
    logger.info(f"Starting voice clip generation for {len(dialogue)} dialogue segments")
    logger.debug(f"Dialogue content: {json.dumps(dialogue, indent=2)}")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    dialogue_queue = queue.Queue()
    for line in dialogue:
        dialogue_queue.put(line)
        if "overlaps" in line:
            for overlap in line.get("overlaps", []):
                dialogue_queue.put(overlap)
    logger.info(f"Added {dialogue_queue.qsize()} items to the queue")

    @backoff.on_exception(backoff.expo,
                          (httpx.HTTPStatusError, httpx.RequestError),
                          max_tries=5,
                          giveup=lambda e: isinstance(e, httpx.HTTPStatusError) and e.response.status_code != 429)
    async def generate_audio(line, previous_text=None):
        speaker = line.get("speaker")
        text = line.get("text")
        voice_id = VOICE_IDS.get(speaker)
        
        logger.info(f"Processing audio for {speaker}: {text[:50]}...")
        
        if not voice_id:
            logger.warning(f"No voice ID found for speaker {speaker}")
            return
            
        filename = get_clip_filename(speaker, text, output_dir)
        if os.path.exists(filename):
            logger.info(f"Audio clip already exists: {filename}")
            return

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVEN_LABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        try:
            logger.debug(f"Sending request to ElevenLabs API for {speaker}")
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{ELEVEN_LABS_API_URL}/{voice_id}",
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                
                with open(filename, "wb") as f:
                    f.write(response.content)
                logger.info(f"Successfully saved audio clip: {filename}")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to generate audio for {speaker}: {e}")
            logger.error(f"Response content: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating audio for {speaker}: {e}")
            raise

    semaphore = asyncio.Semaphore(2)
    tasks = []
    previous_text = None

    while not dialogue_queue.empty():
        line = dialogue_queue.get()
        await semaphore.acquire()
        task = asyncio.create_task(generate_audio(line, previous_text))
        task.add_done_callback(lambda _: semaphore.release())
        tasks.append(task)
        previous_text = line.get("text")

    logger.info(f"Starting to process {len(tasks)} audio generation tasks")
    for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Generating audio clips"):
        await task
    logger.info("Completed all audio generation tasks")

def join_audio_clips(dialogue: List[Dict[str, Any]], output_dir: str = AUDIO_DIR, output_file: str = "final_podcast.wav"):
    output_audio = AudioSegment.silent(duration=0)
    output_path = os.path.join(output_dir, output_file)
    logger.info(f"Starting to join audio clips from {output_dir}")
    logger.debug(f"Dialogue content: {json.dumps(dialogue, indent=2)}")

    for line in tqdm(dialogue, desc="Joining audio clips"):
        speaker = line.get("speaker")
        text = line.get("text")
        filename = get_clip_filename(speaker, text, output_dir)
        
        logger.info(f"Processing clip for {speaker}: {filename}")
        
        try:
            clip = AudioSegment.from_mp3(filename)
            logger.info(f"Loaded clip for {speaker}: {filename} (duration: {len(clip)}ms)")
        except FileNotFoundError:
            logger.error(f"Audio clip not found: {filename}")
            continue
        except Exception as e:
            logger.error(f"Error loading audio clip {filename}: {e}")
            continue

        if "overlaps" in line:
            logger.info(f"Processing overlaps for {speaker}")
            for overlap in line.get("overlaps", []):
                overlap_speaker = overlap.get("speaker")
                overlap_text = overlap.get("text")
                overlap_filename = get_clip_filename(overlap_speaker, overlap_text, output_dir)
                
                try:
                    overlap_clip = AudioSegment.from_mp3(overlap_filename)
                    overlap_start_time = max(0, len(clip) - 850)
                    clip = clip.overlay(overlap_clip, position=overlap_start_time)
                    
                    if len(overlap_clip) > 850:
                        remaining_overlap = overlap_clip[850:]
                        clip = clip.append(remaining_overlap, crossfade=0)
                    logger.info(f"Processed overlap for {overlap_speaker}: {overlap_filename}")
                except FileNotFoundError:
                    logger.error(f"Overlap audio clip not found: {overlap_filename}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing overlap clip {overlap_filename}: {e}")
                    continue

        crossfade_duration = min(10, len(clip) // 2, len(output_audio) // 2) if len(clip) >= 10 and len(output_audio) >= 10 else 0
        output_audio = output_audio.append(clip, crossfade=crossfade_duration)
        logger.info(f"Added clip to output (total duration: {len(output_audio)}ms)")

    logger.info(f"Exporting final audio to: {output_path}")
    output_audio.export(output_path, format="wav")
    logger.info(f"Final audio saved to: {output_path} (duration: {len(output_audio)}ms)")
    return output_path

# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Test dialogue
    input_dialogue = [
  {
    "speaker": "Jessica",
    "text": "Welcome back to 'Tech Forward'! Today, we're diving into something that affects almost everything we buy: the supply chain. We hear about issues like counterfeit goods flooding the market \u2013 apparently over half a *trillion* dollars worth in 2016 \u2013 or those scary food contamination recalls, like the Chipotle E. coli outbreak a few years back."
  },
  {
    "speaker": "Michael",
    "text": "Exactly, Jessica. Knowing where products come from and where they've been \u2013 traceability \u2013 is a huge challenge, especially with global supply chains getting so complex. It's not just about money; it's about safety and trust."
  },
  {
    "speaker": "Jessica",
    "text": "And technology, specifically blockchain, has been proposed as a solution, right? Creating this kind of unchangeable digital record of a product's journey."
  },
  {
    "speaker": "Michael",
    "text": "That's the idea. Using a public blockchain, or PBC, means everyone involved can share the same database of information, like ownership transfers. Because it's immutable \u2013 nobody can tamper with past records \u2013 it builds trust and provides strong traceability."
  }
]

    # Generate voice clips
    asyncio.run(generate_voice_clips(input_dialogue, "audio_clips"))

    # Join audio clips
    join_audio_clips(input_dialogue, "audio_clips", "final_podcast.wav")