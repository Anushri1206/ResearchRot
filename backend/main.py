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