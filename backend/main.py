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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from google.genai.types import GenerateContentConfig, HttpOptions

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

        DIALOGUE_PROMPT = """You are a world-class dialogue producer tasked with transforming the provided input text into an engaging and informative conversation among multiple participants (ranging from 2 to 5 people). The input may be unstructured or messy, sourced from PDFs or web pages. Your goal is to extract the most interesting and insightful content for a compelling discussion.

The input text will be provided in <input_text> tags.
MAKE SURE THAT THERE ARE NOT MORE THAN 5 BACK AND FORTHS. KEEP IT SHORT AND CONCISE.

You will be either required to create scratchpad ideas or write the dialogue based on the scratchpad ideas and the input text.

Scratchpad ideas will be provided in <scratchpad> tags.

You will also be provided with a list of speakers and their properties.

**Steps to Follow:**

1. **Analyze the Input:** Carefully examine the text, identifying key topics, points, and interesting facts or anecdotes that could drive an engaging conversation. Disregard irrelevant information or formatting issues.

2. **Brainstorm Ideas:** In the `<scratchpad>`, creatively brainstorm ways to present the key points engagingly. Consider:
   - Analogies, storytelling techniques, or hypothetical scenarios to make content relatable.
   - Ways to make complex topics accessible to a general audience.
   - Thought-provoking questions to explore during the conversation.
   - Creative approaches to fill any gaps in the information.

3. **Craft the Dialogue in Nested JSON Format:** Develop a natural, conversational flow among the participants, using a nested JSON structure to represent overlapping speech.

   **Format for the Dialogue:**

   - **Overall Structure:** The dialogue is a JSON array containing dialogue turn objects.
   - **Dialogue Turn Object Fields:**
     - `"speaker"`: Name of the speaker.
     - `"text"`: Dialogue text (no more than 800 characters).
     - `"overlaps"`: (Optional) Array of overlapping dialogue turn objects.
       - Each overlapping dialogue turn object can include its own `"overlaps"` array for further nesting if necessary.

   **Example:**

   ```json
   [
     {
       "speaker": "Emma",
       "text": "Welcome, everyone! Let's dive into today's topic."
     },
     {
       "speaker": "Liam",
       "text": "Can't wait to get started!",
       "overlaps": [
         {
           "speaker": "Olivia",
           "text": "Absolutely, it's going to be exciting."
         },
         {
           "speaker": "Noah",
           "text": "I've been looking forward to this all week!"
         }
       ]
     },
     {
       "speaker": "Emma",
       "text": "Great enthusiasm! So, our first question is..."
     }
   ]

4. Rules for the Dialogue:
    - Participant Names: Use made-up names to create an immersive experience.
    - Hosts: If there are hosts (maximum of 2), they initiate and guide the conversation.
    - Interaction: Include thoughtful questions and encourage natural back-and-forth.
    - Natural Speech: Incorporate fillers and speech patterns (e.g., "um," "you know").
    - Overlaps: Represent overlapping speech using the "overlaps" field.
    - Content Accuracy: Ensure contributions are substantiated by the input text.
    - Appropriateness: Maintain PG-rated content suitable for all audiences.
    - Conclusion: End the conversation naturally without forced recaps.

5. Summarize Key Insights: Naturally weave a summary of key points into the dialogue's closing part. This should feel casual and reinforce the main takeaways before signing off.

6. Maintain Authenticity: Include:
    - Moments of genuine curiosity or surprise.
    - Brief struggles to articulate complex ideas.
    - Light-hearted humor where appropriate.
    - Personal anecdotes related to the topic (within the input text bounds).

7. Consider Pacing and Structure: Ensure a natural flow:
    - Hook: Start strong to grab attention.
    - Build-Up: Gradually increase complexity.
    - Breathers: Include moments for listeners to absorb information.
    - Conclusion: End on a high note or thought-provoking point.
    - Overlap: Overlaps in longer text should be used to show a discussion between two people.

8. Enhance Natural Speech Flow with Pauses and Interactions:

   - Use Dashes (`-` or `—`) for Brief Pauses:
     - Incorporate dashes within dialogue to indicate short pauses, mimicking natural speech patterns.
       - *Example:*
         ```json
         {
           "speaker": "Alex",
           "text": "I think we should - maybe - consider other options."
         }
         ```

   - Use Ellipses (`...`) for Hesitations or Uncertainty:
     - Include ellipses to represent hesitations, thinking pauses, or uncertainty.
       - *Example:*
         ```json
         {
           "speaker": "Jamie",
           "text": "I'm not sure if that's... the best approach."
         }
         ```

   - Represent Overlapping Speech for Interactions:
     - Utilize the `"overlaps"` field to depict interruptions or simultaneous speech, enhancing the conversational dynamics.
       - *Example:*
         ```json
         [
           {
             "speaker": "Taylor",
             "text": "We could start with the initial findings and then—",
             "overlaps": [
               {
                 "speaker": "Jordan",
                 "text": "Actually, I think we should re-examine the data first."
               }
             ]
           }
         ]
         ```

   - Incorporate Natural Speech Patterns:
     - Use conversational fillers and colloquial expressions to make the dialogue sound authentic and engaging.
       - *Examples:*
         ```json
         {
           "speaker": "Morgan",
           "text": "You know, it's kind of tricky to explain."
         },
         {
           "speaker": "Riley",
           "text": "Well, let's see... maybe we can figure it out together."
         }
         ```

9. Maintain Clarity in JSON Formatting:

    - Integrate Pauses and Overlaps Smoothly:
      - Ensure that dashes, ellipses, and overlaps are included appropriately within the `"text"` field, keeping the JSON structure valid.
    - Avoid Unintended Read-Aloud Text:
      - Be mindful that the symbols used for pauses and overlaps are interpreted correctly during speech synthesis and do not cause unintended artifacts in the audio output.
    - Example of Combined Usage:
      ```json
      [
        {
          "speaker": "Ella",
          "text": "So, what are our next steps - any ideas?"
        },
        {
          "speaker": "Liam",
          "text": "Well... we could reassess the timeline.",
          "overlaps": [
            {
              "speaker": "Sophia",
              "text": "Or perhaps allocate more resources?"
            }
          ]
        },
        {
          "speaker": "Ella",
          "text": "That's a good point - let's consider both options."
        }
      ]
      ```

IMPORTANT RULES:

- JSON Formatting: The dialogue must be valid JSON for easy parsing.
- Overlaps Representation: Use the "overlaps" field to denote overlapping speech.
- Line Length: Each "text" field should be no more than 800 characters.
- Flexibility: Since exact timings aren't available, adjust overlaps during audio production based on speech duration.
- Output Design: The dialogue is intended for audio conversion; write accordingly.
- Number of Speakers: The number of speakers should be between 2 and 4. A lot speakers will make things messy as voices will keep on changing.
- Natural Language: The dialogue should be in natural language and not robotic use points 8 and 9 to make it sound natural when generating the dialogue.
The two speakers are Jessica and Michael.
<scratchpad> Write your brainstorming ideas and a rough outline for the dialogue here. Note the key insights and takeaways to reiterate at the end. Also provide names for sepaker and speaker ids.
The following are the speakers and their properties:
- Female, soft and caring voice. American, Casual, Young, Female, Conversational. Id: fNmfW5GlQ7PDakGkiTzs
- Male, American, Casual, Middle-aged. Id: iP95p4xoKVk53GoZ742B


When generating the scratchpad ideas, if a user message is provided please think of ideas based on that message or instructions. The instruction(s) can only apply if the PDF content has text related to the instruction(s). If the content does not have text related to the instruction(s), ignore the instruction(s).
User instruction will be provided in <user_instruction> tags.
</scratchpad>
<dialogue> Write your engaging, informative dialogue here in the specified nested JSON format, based on your brainstorming session's key points and creative ideas. Ensure the content is accessible and engaging for a general audience.
Aim for a long, detailed dialogue while staying on topic and maintaining an engaging flow. Use your full output capacity to communicate the key information effectively and entertainingly.

At the end of the dialogue, have the participants naturally summarize the main insights and takeaways. This should flow organically, reinforcing the central ideas casually before concluding. </dialogue>"""

        if input_type == "url":
            full_prompt = f"""<input_text>
{input_content}
</input_text>

<user_instruction>
{prompt}
</user_instruction>

{DIALOGUE_PROMPT}"""

            dialogue = call_gemini(prompt=full_prompt, system_message=system_message)
        else:
            # files = upload_to_gemini(input_content, "application/pdf") # Missing Function
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
                        transcript=transcript,
                        audio_file="",
                        status="error",
                        error="Failed to generate audio file"
                    )
                logger.info(f"Joined audio clips into: {final_audio_path}")
                
                # Read the audio file and convert to base64
                try:
                    if not os.path.exists(final_audio_path):
                        logger.error(f"Audio file not found at path: {final_audio_path}")
                        return PodcastResponse(
                            transcript=transcript,
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
                        transcript=transcript,
                        audio_file="",
                        status="error",
                        error="Failed to process audio file"
                    )

                return PodcastResponse(
                    transcript=dialogue_list,
                    audio_file=audio_base64,
                    status="success"
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON transcript: {e}")
                return PodcastResponse(
                    transcript=transcript,
                    audio_file="",
                    status="error",
                    error="Failed to parse podcast transcript"
                )
        else:
            logger.error("Could not find <dialogue> section in the text")
            return PodcastResponse(
                transcript=transcript,
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