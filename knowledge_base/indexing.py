
# knowledge_base/indexing.py
import json
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from utils.config import (
    PROCESSED_DATA_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL,
    CHROMA_PATH,
    COLLECTION_NAME
)
from .text_processing import preprocess_documents

def load_and_process_data(file_path: str = PROCESSED_DATA_PATH) -> list[dict]:
    """載入、預處理並回傳文件。"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            documents = json.load(f)
    except FileNotFoundError:
        print(f"Error: Data file not found at {file_path}")
        return []
    
    return preprocess_documents(documents)

def chunk_documents(documents: list[dict]) -> list[Document]:
    """將文件切塊並保留元資料。"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    chunks = []
    for doc in documents:
        if not doc.get('content'):
            continue
        # LangChain 的 splitter 會處理文本切分
        splits = text_splitter.split_text(doc['content'])
        for split in splits:
            # 為每個 chunk 建立一個新的 Document 物件，並複製 metadata
            metadata = {
                "source": doc.get('source', 'unknown'),
                "url": doc.get('url', ''),
                "title": doc.get('title', ''),
                "scraped_at": doc.get('scraped_at', ''),
                "publication_date": doc.get('publication_date', '')
            }
            chunk_doc = Document(page_content=split, metadata=metadata)
            chunks.append(chunk_doc)
    return chunks

def build_vector_store(chunks: list[Document]):
    """建立並儲存向量資料庫。"""
    print(f"Creating embeddings with model: {EMBEDDING_MODEL}")
    print(f"Storing vector store at: {CHROMA_PATH}")
    
    # 建立 embedding 函式
    embedding_function = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)
    
    # 建立 ChromaDB client
    # 這會將資料庫持久化到磁碟
    vector_store = Chroma.from_documents(
        documents=chunks, 
        embedding=embedding_function,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_PATH
    )
    
    print(f"Successfully built and saved vector store with {len(chunks)} chunks.")
    return vector_store

def build_knowledge_base():
    """執行完整的知識庫建立流程。"""
    documents = load_and_process_data()
    if not documents:
        print("No documents to process. Exiting knowledge base build.")
        return
    
    chunks = chunk_documents(documents)
    if not chunks:
        print("No chunks were created from the documents. Exiting.")
        return
        
    build_vector_store(chunks)

if __name__ == '__main__':
    # 可以直接執行此腳本來建立知識庫
    build_knowledge_base()
