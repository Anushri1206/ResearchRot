import os
from dotenv import load_dotenv
import requests
import PyPDF2
import io
import traceback
from google import genai
# Remove: from google.generativeai import types
import logging
import re
from pydub import AudioSegment
import tempfile
import json
import asyncio
from voiceover import generate_voice_clips, join_audio_clips
import base64
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import numpy as np
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from google.genai.types import GenerateContentConfig, HttpOptions
from prompts import BRAINROT_PROMPT, PODCAST_PROMPT

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class Query(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None
    is_arxiv: Optional[bool] = False
    context: Optional[str] = None
    file_content: Optional[str] = None


class Response(BaseModel):
    answer: str
    sources: Optional[List[str]] = None
    error: Optional[str] = None  # Add error field


class PodcastRequest(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None
    is_arxiv: Optional[bool] = False
    prompt: Optional[str] = None
    input_type: str = "url"


class PodcastResponse(BaseModel):
    transcript: str
    audio_file: str
    status: str


class BrainRotRequest(BaseModel):
    pdf_url: str
    text_color: str = "white"
    font_size: int = 200
    duration_per_phrase: float = 3.0
    position: str = "center"


class BrainRotResponse(BaseModel):
    video_file: str
    status: str
    error: Optional[str] = None


def download_pdf(url: str) -> str:
    """Download PDF from URL and extract text."""
    try:
        logger.info(f"Downloading PDF from: {url}")  # Use logger
        response = requests.get(url)
        response.raise_for_status()

        logger.info("PDF downloaded successfully, extracting text...")
        pdf_file = io.BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        
        # Extract text from all pages

        # Extract text from all pages
        text = ""
        for i, page in enumerate(pdf_reader.pages):
            logger.info(f"Processing page {i + 1}/{len(pdf_reader.pages)}")
            text += page.extract_text() + "\n"

        logger.info("Text extraction completed")
        return text

    except requests.exceptions.RequestException as e:  # Specific exception
        logger.error(f"Download failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download PDF: {e}")
    except PyPDF2.errors.PdfReadError as e:  # Specific exception
        logger.error(f"PDF processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in download_pdf: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")  # Generic message


def process_text(text: str) -> str:
    """Process and clean the input text."""
    return text.strip()


def call_gemini(prompt: str, system_message: str) -> str:
    """Calls the Gemini model."""
    logger.info("Calling Gemini model...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro-exp-03-25",
            contents=prompt,
            config=GenerateContentConfig(system_instruction=system_message),
        )
        logger.info("Gemini model returned output")
        print(response.text)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini API call failed: {e}")



def podcast_generator(prompt: str, system_message: str, input_content: str, input_type: str) -> dict:
    """Generates a podcast transcript."""

    try:
        logger.info("Generating podcast dialogue...")

        if input_type == "url":
            full_prompt = f"""<input_text>
{input_content}
</input_text>

<user_instruction>
{prompt}
</user_instruction>

{PODCAST_PROMPT}"""

            dialogue = call_gemini(prompt=full_prompt, system_message=system_message)
        else:
            dialogue = call_gemini(prompt=prompt, system_message=system_message)

        if not dialogue:
            logger.warning("No dialogue generated")
            raise ValueError("No dialogue generated")
        return {
            "transcript": dialogue
        }

    except Exception as e:
        logger.error(f"Podcast generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating podcast: {e}")


@app.post("/generate_podcast", response_model=PodcastResponse)
async def generate_podcast_endpoint(request: PodcastRequest):
    """Generates a podcast based on the provided request."""
    try:
        logger.info("Received request to generate podcast")
        
        # Get input content based on type
        if request.input_type == "url" and request.url:
            if request.is_arxiv:
                pdf_url = request.url.replace('/abs/', '/pdf/') + '.pdf'
                input_content = download_pdf(pdf_url)
            else:
                response = requests.get(request.url)
                response.raise_for_status()
                input_content = response.text
        elif request.text:
            input_content = request.text
        else:
            raise HTTPException(status_code=400, detail="No input provided")

        # Generate podcast transcript
        prompt = request.prompt or """Create a podcast dialogue based on the following content. 
        Format the response as a conversation between two speakers, followed by their dialogue.
        Make it sound like a real podcast with natural conversation flow.
        
        Content:
        {input_content}"""

        system_instructions = """You are a podcast script generator. Create engaging and natural-sounding dialogue 
        between two speakers discussing the given content. Make it sound like a real podcast conversation."""

        # Generate the podcast transcript
        response = podcast_generator(prompt=prompt, system_message=system_instructions, input_content=input_content, input_type=request.input_type)
        transcript = response["transcript"]
        cleaned_text = transcript.replace("*", "")
        logger.info("Generated podcast transcript")
        print(transcript, "transcript")
        
        match = re.search(r"<dialogue>\s*(\[.*?\])\s*</dialogue>", cleaned_text, re.DOTALL)

        if match:
            dialogue_json_str = match.group(1)
            try:
                dialogue_list = json.loads(dialogue_json_str)
                print("✅ Successfully extracted dialogue list:")
                print(dialogue_list)
                
                # Generate voice clips
                await generate_voice_clips(dialogue_list)
                logger.info("Generated voice clips")
                
                # Join audio clips
                final_audio_path = join_audio_clips(dialogue_list)
                if not final_audio_path:
                    logger.error("Failed to generate final audio path")
                    return PodcastResponse(
                        transcript=str(dialogue_list),  # Convert to string
                        audio_file="",
                        status="error",
                        error="Failed to generate audio file"
                    )
                logger.info(f"Joined audio clips into: {final_audio_path}")
                
                try:
                    if not os.path.exists(final_audio_path):
                        logger.error(f"Audio file not found at path: {final_audio_path}")
                        return PodcastResponse(
                            transcript=str(dialogue_list),  # Convert to string
                            audio_file="",
                            status="error",
                            error="Audio file not found"
                        )
                        
                    with open(final_audio_path, "rb") as f:
                        audio_data = f.read()
                        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    logger.info("Successfully converted audio to base64")
                except Exception as e:
                    logger.error(f"Failed to read and convert audio file: {e}")
                    return PodcastResponse(
                        transcript=str(dialogue_list),  # Convert to string
                        audio_file="",
                        status="error",
                        error="Failed to process audio file"
                    )

                return PodcastResponse(
                    transcript=str(dialogue_list),  # Convert to string
                    audio_file=audio_base64,
                    status="success"
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON transcript: {e}")
                return PodcastResponse(
                    transcript=str(transcript),  # Use original transcript as string
                    audio_file="",
                    status="error",
                    error="Failed to parse podcast transcript"
                )
        else:
            logger.error("Could not find <dialogue> section in the text")
            return PodcastResponse(
                transcript=str(transcript),  # Use original transcript as string
                audio_file="",
                status="error",
                error="Could not find dialogue section in transcript"
            )

    except Exception as e:
        logger.exception("Unexpected error during podcast generation")
        return PodcastResponse(
            transcript="",
            audio_file="",
            status="error",
            error=str(e)
        )


@app.post("/query", response_model=Response)
async def process_query(query: Query):
    """Processes a user query."""
    try:
        logger.info(f"Received query: {query}")
        if query.url and query.is_arxiv:
            logger.info("Processing arXiv URL")
            pdf_text = download_pdf(query.url)
            processed_text = process_text(pdf_text)
            logger.info(f"Extracted text length: {len(processed_text)} characters")
        else:
            logger.info("Processing regular text")
            processed_text = process_text(query.text or "")

        logger.info("Sending to Gemini model...")
        response = client.models.generate_content(
            model="gemini-2.5-pro-exp-03-25",
            contents=processed_text
        )

        logger.info("Received response from Gemini")
        return Response(answer=response.text)

    except Exception as e:
        logger.exception(f"Error processing query: {e}")  # Log the exception and traceback
        return Response(answer="", error=str(e))  # Return error information

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/generate_brainrot", response_model=BrainRotResponse)
async def generate_brainrot(
    request: str = Form(...)
):
    """Generates a brain rot style video with text from PDF URL."""
    try:
        logger.info("Starting brain rot video generation")
        
        # Parse the request data
        try:
            request_data = json.loads(request)
            logger.info(f"Parsed request data: {request_data}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse request data: {str(e)}")
            return BrainRotResponse(
                video_file="",
                status="error",
                error="Invalid request data format"
            )

        # Process PDF and generate script
        logger.info("Processing PDF and generating script")
        try:
            # Download and extract text from PDF
            pdf_text = download_pdf(request_data['pdf_url'])
            logger.info("Successfully extracted text from PDF")

            # Generate script using Gemini
            prompt = BRAINROT_PROMPT.format(content=pdf_text)

            script_response = call_gemini(
                prompt=prompt,
                system_message="You are a content creator specializing in viral, attention-grabbing content. Convert the given text into short, engaging phrases suitable for a brain rot style video."
            )

            # Parse the response into phrases
            try:
                # Clean up the response by removing markdown code block markers
                cleaned_response = script_response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]  # Remove ```
                cleaned_response = cleaned_response.strip()
                
                phrases = json.loads(cleaned_response)
                if not isinstance(phrases, list):
                    raise ValueError("Response is not a list")
                logger.info(f"Generated {len(phrases)} phrases from PDF")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response: {str(e)}")
                logger.error(f"Response content: {script_response}")
                return BrainRotResponse(
                    video_file="",
                    status="error",
                    error="Failed to generate script from PDF"
                )

        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return BrainRotResponse(
                video_file="",
                status="error",
                error="Failed to process PDF"
            )

        # Generate voice clips for each phrase
        logger.info("Generating voice clips")
        try:
            # Combine all phrases into a single text
            combined_text = " ".join(phrases)
            
            # Create a single dialogue entry
            dialogue = [{
                "speaker": "Jessica",
                "text": combined_text,
                "voice_id": "fNmfW5GlQ7PDakGkiTzs"  # Female voice ID
            }]
            
            # Generate single voice clip
            await generate_voice_clips(dialogue)
            logger.info("Generated voice clip")
            
            # Get the audio path
            final_audio_path = join_audio_clips(dialogue)
            if not final_audio_path:
                logger.error("Failed to generate final audio path")
                return BrainRotResponse(
                    video_file="",
                    status="error",
                    error="Failed to generate audio file"
                )
            logger.info(f"Generated audio at: {final_audio_path}")

        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            return BrainRotResponse(
                video_file="",
                status="error",
                error="Failed to generate audio"
            )

        # Process video and add text overlays
        logger.info("Processing video with generated phrases and audio")
        try:
            # Use default video from static folder
            default_video_path = os.path.join("static", "input.mov")
            if not os.path.exists(default_video_path):
                logger.error(f"Default video not found at path: {default_video_path}")
                return BrainRotResponse(
                    video_file="",
                    status="error",
                    error="Default background video not found"
                )

            # Load the video
            video_clip = VideoFileClip(default_video_path)
            
            # Load the audio
            audio_clip = AudioFileClip(final_audio_path)
            
            # Create text clips for each phrase
            text_clips = []
            for i, phrase in enumerate(phrases):
                start_time = i * request_data.get('duration_per_phrase', 2.0)
                
                txt_clip = TextClip(
                    phrase,
                    fontsize=request_data.get('font_size', 200),
                    color=request_data.get('text_color', 'white'),
                    bg_color='transparent',
                    font='Arial-Bold',
                    method='caption'
                )
                
                txt_clip = txt_clip.set_position(request_data.get('position', 'center'))
                txt_clip = txt_clip.set_duration(request_data.get('duration_per_phrase', 2.0))
                txt_clip = txt_clip.set_start(start_time)
                
                text_clips.append(txt_clip)

            # Create final video with audio
            final_video = CompositeVideoClip([video_clip] + text_clips)
            final_video = final_video.set_audio(audio_clip)
            
            # Save the result
            output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
            final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
            
            # Clean up
            video_clip.close()
            audio_clip.close()
            final_video.close()
            
            # Convert to base64
            with open(output_path, "rb") as f:
                video_data = f.read()
                video_base64 = base64.b64encode(video_data).decode('utf-8')
            
            # Clean up temporary files
            os.unlink(output_path)
            os.unlink(final_audio_path)
            
            return BrainRotResponse(
                video_file=video_base64,
                status="success"
            )
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            return BrainRotResponse(
                video_file="",
                status="error",
                error="Failed to process video"
            )
            
    except Exception as e:
        logger.error(f"Error generating brain rot video: {str(e)}")
        return BrainRotResponse(
            video_file="",
            status="error",
            error=str(e)
        ) 