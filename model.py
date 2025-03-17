import os
from flask import Flask, request, jsonify
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyMuPDFLoader
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
import requests
import json
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
GROQ_API_KEY = os.getenv("GROQ_TOKEN")

# Set up Groq API
os.environ["OPENAI_API_KEY"] = GROQ_API_KEY
os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"

# Load Llama3 on Groq
llm = ChatOpenAI(model_name="llama3-8b-8192", temperature=0.3)

# Load PDF document
pdf_path = "ammar-resume.pdf"  # Replace with your PDF file path
loader = PyMuPDFLoader(pdf_path)
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
docs = text_splitter.split_documents(documents)

embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

vectorstore = FAISS.from_documents(docs, embedding)

retriever = vectorstore.as_retriever()
rag_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type="stuff")


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
@app.route('/query')
def chat_with_llama(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 200
    }
    
    response = requests.post(GROQ_API_URL, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "No response")
    else:
        return f"Error: {response.status_code} - {response.text}"

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
