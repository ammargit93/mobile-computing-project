import os
from flask import Flask, request, jsonify
from langchain_groq.chat_models import ChatGroq  # Changed to use Groq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader, Docx2txtLoader
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
import requests
import json
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()
app = Flask(__name__)

GROQ_API_KEY = "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"
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

llm = ChatGroq(temperature=0.3, groq_api_key=GROQ_API_KEY, model_name="llama3-8b-8192") 
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

vectorstore = None
qa_chain = None
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_and_process_documents(file_path):
    """Load and process documents based on file type"""
    if file_path.endswith('.pdf'):
        loader = PyMuPDFLoader(file_path)
    elif file_path.endswith('.txt'):
        loader = TextLoader(file_path)
    elif file_path.endswith('.docx'):
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError("Unsupported file type")
    
    documents = loader.load()
    return text_splitter.split_documents(documents)

def initialize_rag_chain(docs):
    global vectorstore, qa_chain
    vectorstore = FAISS.from_documents(docs, embedding)
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory,
        chain_type="stuff"
    )
    return "RAG system initialized successfully"

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            docs = load_and_process_documents(filepath)
            result = initialize_rag_chain(docs)
            return jsonify({"message": result, "filename": filename}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "File type not allowed"}), 400

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint with RAG"""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Message is required"}), 400
    
    user_message = data['message']
    
    # Use direct Groq API if RAG isn't initialized
    if qa_chain is None:
        return jsonify({
            "response": chat_with_groq(user_message),
            "source": "Direct LLM response (no RAG)"
        })
    
    # Use RAG chain if available
    try:
        result = qa_chain({"question": user_message})
        return jsonify({
            "response": result['answer'],
            "source": "RAG-enhanced response",
            "context": result.get('source_documents', [])
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def chat_with_groq(prompt):
    """Fallback to direct Groq API if RAG isn't available"""
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
    
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload)
    )
    print(response.json())
    if response.status_code == 200:
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "No response")
    return f"Error: {response.status_code} - {response.text}"

@app.route('/reset', methods=['POST'])
def reset_conversation():
    """Reset conversation history"""
    global memory
    memory.clear()
    return jsonify({"message": "Conversation history cleared"}), 200

if __name__ == "__main__":
    app.run(host="localhost", port=7000, debug=True)