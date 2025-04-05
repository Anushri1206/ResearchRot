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

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def create_qa_chain(context: str = None, file_content: str = None):
    """Create a QA chain with the given context."""
    if not context and not file_content:
        return None
    
    text = context or file_content
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    texts = text_splitter.split_text(text)
    
    embeddings = OpenAIEmbeddings()
    docsearch = FAISS.from_texts(texts, embeddings)
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(
            model_name=os.getenv("MODEL_NAME"),
            temperature=float(os.getenv("TEMPERATURE"))
        ),
        chain_type="stuff",
        retriever=docsearch.as_retriever()
    )
    
    return qa_chain

@app.post("/query", response_model=Response)
async def process_query(query: Query):
    try:
        # Process the input
        processed_text = process_text(query.text)
        
        # If we have context or file content, use QA chain
        if query.context or query.file_content:
            qa_chain = create_qa_chain(query.context, query.file_content)
            if qa_chain:
                result = qa_chain({"query": processed_text})
                return Response(answer=result["result"])
        
        # Otherwise, use direct OpenAI completion
        response = client.chat.completions.create(
            model=os.getenv("MODEL_NAME"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": processed_text}
            ],
            max_tokens=int(os.getenv("MAX_TOKENS")),
            temperature=float(os.getenv("TEMPERATURE"))
        )
        
        return Response(answer=response.choices[0].message.content)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 