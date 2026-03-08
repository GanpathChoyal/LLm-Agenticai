import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

def create_vector_store():
    data_dir = os.path.join(os.path.dirname(__file__), "guidelines")
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./rag/chroma_db")
    
    docs = []
    if os.path.exists(data_dir):
        for file in os.listdir(data_dir):
            if file.endswith(".pdf"):
                loader = PyPDFLoader(os.path.join(data_dir, file))
                docs.extend(loader.load())
    
    if not docs:
        print("No PDFs found. Creating mock guidelines index.")
        from langchain_core.documents import Document
        docs = [Document(page_content="ESC/AHA Guidelines: 1. Evaluate early ECG. 2. Use 0h/1h high-sensitivity troponin algorithm. 3. Immediate reperfusion for STEMI.")]
        
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory=persist_dir)
    vectorstore.persist()
    print("Vector store created successfully.")

if __name__ == "__main__":
    create_vector_store()
