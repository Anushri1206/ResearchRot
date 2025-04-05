from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from google import genai
load_dotenv()

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
    text: str
    context: Optional[str] = None
    file_content: Optional[str] = None

class Response(BaseModel):
    answer: str
    sources: Optional[List[str]] = None

def process_text(text: str) -> str:
    """Process and clean the input text."""
    return text.strip()
def call_gemini(prompt: str, system_message: str) -> str:
    logger.info("Calling Gemini model...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro-exp-03-25",
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=system_message),
        )
        print(response.text)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API call failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gemini API call failed: {str(e)}")

def generate_audio_from_text(text: str, output_path: str = "podcast_audio.mp3") -> str:
    """
    Stub for audio generation — replace with actual TTS implementation.
    """
    logger.info("Generating audio from text (stub)...")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        logger.info(f"Audio saved to: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Audio generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")

def podcast_generator(prompt: str, system_message: str, input_content: str, input_type: str) -> dict:
    try:
        logger.info("Generating podcast dialogue...")
        if input_type == "url":
            # For URL content, create a more structured prompt
            full_prompt = f"""Please create a podcast dialogue based on the following content from the URL:

Content:
{input_content}

Instructions:
1. Create a dialogue between male-1 and female-1
2. Format each line as "male-1: [text]" or "female-1: [text]"
3. Keep the conversation natural and engaging
4. Focus on the key points from the content
5. Make it sound like a real podcast discussion

{prompt}"""
            
            dialogue = call_gemini(prompt=full_prompt, system_message=system_message)
        else:
            files = upload_to_gemini(input_content, "application/pdf")
            dialogue = call_gemini(prompt=prompt, system_message=system_message)

        if not dialogue:
            logger.warning("No dialogue generated")
            raise ValueError("No dialogue generated")

        # Parse dialogue into items
        dialogue_items = []
        for line in dialogue.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("male-1:"):
                speaker = "male-1"
                text = line[len("male-1:"):].strip()
            elif line.startswith("female-1:"):
                speaker = "female-1"
                text = line[len("female-1:"):].strip()
            else:
                continue
            
            dialogue_items.append(DialogueItem(text=text, speaker=speaker))

        if not dialogue_items:
            logger.warning("No valid dialogue items found")
            raise ValueError("No valid dialogue items found")

        return {
            "transcript": dialogue
        }

    except Exception as e:
        logger.error(f"Podcast generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating podcast: {str(e)}")

# --- API Endpoints ---
@app.post("/generate_podcast", response_model=PodcastResponse)
async def generate_podcast_endpoint(request: PodcastRequest):
    try:
        logger.info("Received request to generate podcast")

        input_content = process_input_content(
            input_type=request.input_type,
            url=request.url, 
            pdf_path=request.pdf_path
        )

        result = podcast_generator(
            prompt=request.prompt,
            system_message=system_instructions,
            input_content=input_content,
            input_type=request.input_type
        )

        transcript_path = "podcast_transcript.txt"
        with open(transcript_path, "w", encoding="utf-8") as transcript_file:
            transcript_file.write(result["transcript"])

        audio_path = generate_audio_from_text(result["transcript"])

        return PodcastResponse(
            transcript=result["transcript"],
            audio_file=audio_path,
            status="success"
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=Response)
async def process_query(query: Query):
    try:
        processed_text = process_text(query.text)
        response = client.models.generate_content(
            model="gemini-2.5-pro-exp-03-25", contents=processed_text
        )
        print(response.text)
        return Response(answer=response.text)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 