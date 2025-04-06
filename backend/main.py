from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
import requests
import PyPDF2
import io
import google.generativeai as genai
import traceback
import json

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize FastAPI app
app = FastAPI()

# Allow frontend (React) requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Query(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None
    is_arxiv: Optional[bool] = False
    context: Optional[str] = None
    file_content: Optional[str] = None

class Response(BaseModel):
    answer: str
    sources: Optional[List[str]] = None

class FlashcardRequest(BaseModel):
    summary: str
    count: int = 10

class Flashcard(BaseModel):
    question: str
    answer: str

class FlashcardResponse(BaseModel):
    flashcards: List[Flashcard]

class MnemonicRequest(BaseModel):
    summary: str
    count: int = 5

class Mnemonic(BaseModel):
    concept: str
    mnemonic: str

class MnemonicResponse(BaseModel):
    mnemonics: List[Mnemonic]

# Download and extract text from PDF
def download_pdf(url: str) -> str:
    try:
        print(f"Attempting to download PDF from: {url}")
        response = requests.get(url)
        response.raise_for_status()

        print("PDF downloaded successfully, extracting text...")
        pdf_file = io.BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        text = ""
        for i, page in enumerate(pdf_reader.pages):
            print(f"Processing page {i+1}/{len(pdf_reader.pages)}")
            text += page.extract_text() + "\n"

        print("Text extraction completed")
        return text
    except Exception as e:
        print(f"Error in download_pdf: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to download or process PDF: {str(e)}")

# Basic text processing
def process_text(text: str) -> str:
    return text.strip()

# Endpoint: summarize a paper
@app.post("/query", response_model=Response)
async def process_query(query: Query):
    try:
        print(f"Received query: {query}")
        if query.url and query.is_arxiv:
            print("Processing arXiv URL")
            pdf_text = download_pdf(query.url)
            processed_text = process_text(pdf_text)
            print(f"Extracted text length: {len(processed_text)} characters")
        else:
            print("Processing regular text")
            processed_text = process_text(query.text or "")

        print("Sending to Gemini model...")
        model = genai.GenerativeModel(model_name="gemini-1.5-pro")
        response = model.generate_content(
            "Summarize the following research paper in a concise but comprehensive way. Focus on the main objectives, methodology, key findings, and conclusions. Keep the summary clear and structured so that someone unfamiliar with the paper can understand the core contributions without needing to read the full text. Limit the summary to around 300-500 words, and avoid unnecessary jargon unless it's essential to the topic.\n\n" + processed_text
        )

        print("Received response from Gemini")
        return Response(answer=response.text)
    
    except Exception as e:
        print(f"Error in process_query: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint: generate flashcards
@app.post("/generate-flashcards", response_model=FlashcardResponse)
async def generate_flashcards(request: FlashcardRequest):
    try:
        print(f"Generating {request.count} flashcards from summary")

        prompt = f"""
        Create exactly {request.count} flashcards based on this research paper summary.
        Each flashcard should have a question on the front and an answer on the back. Make the questions and answers concise and to the point.
        The questions should test understanding of key concepts, findings, and methodologies.
        Format the output as a JSON array of objects, each with 'question' and 'answer' fields.
        Make sure to generate exactly {request.count} flashcards, no more and no less.
        DO NOT include any markdown formatting or code blocks in your response.
        Return ONLY the JSON array, nothing else.

        Summary: {request.summary}
        """

        model = genai.GenerativeModel(model_name="gemini-1.5-pro")
        response = model.generate_content(prompt)
        
        print(f"Raw response from Gemini: {response.text[:200]}...")

        try:
            # Try to extract JSON from the response
            json_str = response.text
            # Find the first '[' and last ']' to extract the JSON array
            start_idx = json_str.find('[')
            end_idx = json_str.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = json_str[start_idx:end_idx]
                print(f"Extracted JSON: {json_str[:100]}...")
                
                # Clean up the JSON string - remove any markdown code blocks
                json_str = json_str.replace('```json', '').replace('```', '')
                
                result = json.loads(json_str)
                
                # Ensure we have the requested number of flashcards
                if len(result) < request.count:
                    print(f"Warning: Only {len(result)} flashcards generated, expected {request.count}")
                    # Add more flashcards if needed
                    while len(result) < request.count:
                        result.append({
                            "question": f"What is an important aspect of this research not covered in other questions?",
                            "answer": "This is a placeholder answer. Please regenerate flashcards to get a complete set."
                        })
                
                flashcards = [
                    Flashcard(
                        question=item.get('question', ''),
                        answer=item.get('answer', '')
                    ) for item in result[:request.count]  # Limit to requested count
                ]
            else:
                print("Could not find JSON array in response")
                # Fallback: Create simple flashcards
                flashcards = []
                sentences = request.summary.split('. ')
                for i in range(min(request.count, len(sentences))):
                    if i < len(sentences):
                        question = f"What is the {i+1}th main point of the research?"
                        answer = sentences[i].strip()
                        flashcards.append(Flashcard(question=question, answer=answer))
                
                # Add more flashcards if needed
                while len(flashcards) < request.count:
                    flashcards.append(Flashcard(
                        question=f"What is an important aspect of this research not covered in other questions?",
                        answer="This is a placeholder answer. Please regenerate flashcards to get a complete set."
                    ))
        except Exception as parse_err:
            print(f"Failed to parse flashcards as JSON: {parse_err}")
            # Fallback: Create simple flashcards
            flashcards = []
            sentences = request.summary.split('. ')
            for i in range(min(request.count, len(sentences))):
                if i < len(sentences):
                    question = f"What is the {i+1}th main point of the research?"
                    answer = sentences[i].strip()
                    flashcards.append(Flashcard(question=question, answer=answer))
            
            # Add more flashcards if needed
            while len(flashcards) < request.count:
                flashcards.append(Flashcard(
                    question=f"What is an important aspect of this research not covered in other questions?",
                    answer="This is a placeholder answer. Please regenerate flashcards to get a complete set."
                ))

        print(f"Generated {len(flashcards)} flashcards")
        return FlashcardResponse(flashcards=flashcards)

    except Exception as e:
        print(f"Error generating flashcards: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint: generate mnemonics
@app.post("/generate-mnemonics", response_model=MnemonicResponse)
async def generate_mnemonics(request: MnemonicRequest):
    try:
        print(f"Generating {request.count} mnemonics from summary")

        prompt = f"""
        Create exactly {request.count} mnemonic devices based on this research paper summary.
        Each mnemonic should help remember a key concept, finding, or methodology from the research.
        Make the mnemonics fun, silly, and Gen Z-friendly. Use pop culture references, internet slang, and relatable analogies.
        The mnemonics should be memorable and help students recall the information during exams.
        Format the output as a JSON array of objects, each with 'concept' and 'mnemonic' fields.
        Make sure to generate exactly {request.count} mnemonics, no more and no less.
        DO NOT include any markdown formatting or code blocks in your response.
        Return ONLY the JSON array, nothing else.

        Summary: {request.summary}
        """

        model = genai.GenerativeModel(model_name="gemini-1.5-pro")
        response = model.generate_content(prompt)
        
        print(f"Raw response from Gemini: {response.text[:200]}...")

        try:
            # Try to extract JSON from the response
            json_str = response.text
            # Find the first '[' and last ']' to extract the JSON array
            start_idx = json_str.find('[')
            end_idx = json_str.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = json_str[start_idx:end_idx]
                print(f"Extracted JSON: {json_str[:100]}...")
                
                # Clean up the JSON string - remove any markdown code blocks
                json_str = json_str.replace('```json', '').replace('```', '')
                
                result = json.loads(json_str)
                
                # Ensure we have the requested number of mnemonics
                if len(result) < request.count:
                    print(f"Warning: Only {len(result)} mnemonics generated, expected {request.count}")
                    # Add more mnemonics if needed
                    while len(result) < request.count:
                        result.append({
                            "concept": "Additional concept from the research",
                            "mnemonic": "This is a placeholder mnemonic. Please regenerate to get a complete set."
                        })
                
                mnemonics = [
                    Mnemonic(
                        concept=item.get('concept', ''),
                        mnemonic=item.get('mnemonic', '')
                    ) for item in result[:request.count]  # Limit to requested count
                ]
            else:
                print("Could not find JSON array in response")
                # Fallback: Create simple mnemonics
                mnemonics = []
                sentences = request.summary.split('. ')
                for i in range(min(request.count, len(sentences))):
                    if i < len(sentences):
                        concept = sentences[i].strip()
                        mnemonic = f"Remember this concept by thinking of it as a TikTok trend: {concept[:50]}..."
                        mnemonics.append(Mnemonic(concept=concept, mnemonic=mnemonic))
                
                # Add more mnemonics if needed
                while len(mnemonics) < request.count:
                    mnemonics.append(Mnemonic(
                        concept="Additional concept from the research",
                        mnemonic="This is a placeholder mnemonic. Please regenerate to get a complete set."
                    ))
        except Exception as parse_err:
            print(f"Failed to parse mnemonics as JSON: {parse_err}")
            # Fallback: Create simple mnemonics
            mnemonics = []
            sentences = request.summary.split('. ')
            for i in range(min(request.count, len(sentences))):
                if i < len(sentences):
                    concept = sentences[i].strip()
                    mnemonic = f"Remember this concept by thinking of it as a TikTok trend: {concept[:50]}..."
                    mnemonics.append(Mnemonic(concept=concept, mnemonic=mnemonic))
            
            # Add more mnemonics if needed
            while len(mnemonics) < request.count:
                mnemonics.append(Mnemonic(
                    concept="Additional concept from the research",
                    mnemonic="This is a placeholder mnemonic. Please regenerate to get a complete set."
                ))

        print(f"Generated {len(mnemonics)} mnemonics")
        return MnemonicResponse(mnemonics=mnemonics)

    except Exception as e:
        print(f"Error generating mnemonics: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
