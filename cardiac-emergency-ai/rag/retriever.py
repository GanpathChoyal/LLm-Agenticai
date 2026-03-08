import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

def retrieve_guidelines(query_list: list) -> str:
    """
    Retrieves the most relevant guidelines from ChromaDB based on patient symptoms.
    """
    try:
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./rag/chroma_db")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # If the DB doesn't exist, fallback mock
        if not os.path.exists(persist_dir):
            return "Mock Guidelines: Immediate reperfusion strategy indicated for suspected STEMI. High-sensitivity troponin requires evaluation."
            
        vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
        
        query = " ".join(query_list) if query_list else "cardiac emergency protocols"
        docs = retriever.invoke(query)
        
        return "\n\n".join([d.page_content for d in docs])
    except Exception as e:
        print(f"RAG Retrieval Error: {e}")
        return "RAG Unavailable. Proceed with standard cardiac protocols."
