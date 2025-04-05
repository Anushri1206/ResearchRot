from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
import requests
import PyPDF2
import io
import traceback
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
    url: Optional[str] = None
    text: Optional[str] = None
    is_arxiv: Optional[bool] = False
    context: Optional[str] = None
    file_content: Optional[str] = None

class Response(BaseModel):
    answer: str
    sources: Optional[List[str]] = None

def download_pdf(url: str) -> str:
    """Download PDF from URL and extract text."""
    try:
        print(f"Attempting to download PDF from: {url}")
        response = requests.get(url)
        response.raise_for_status()
        
        print("PDF downloaded successfully, extracting text...")
        # Read PDF from the response content
        pdf_file = io.BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
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

def process_text(text: str) -> str:
    """Process and clean the input text."""
    return text.strip()

@app.post("/query", response_model=Response)
async def process_query(query: Query):
    try:
        print(f"Received query: {query}")
        if query.url and query.is_arxiv:
            print("Processing arXiv URL")
            # Download and process PDF from arXiv URL
            pdf_text = download_pdf(query.url)
            processed_text = process_text(pdf_text)
            print(f"Extracted text length: {len(processed_text)} characters")
        else:
            print("Processing regular text")
            processed_text = process_text(query.text or "")

        print("Sending to Gemini model...")
        # Generate response using Gemini
        response = client.models.generate_content(
            model="gemini-2.5-pro-exp-03-25",
            contents=processed_text
        )
        
        print("Received response from Gemini")
        return Response(answer=response.text)
    
    except Exception as e:
        print(f"Error in process_query: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 