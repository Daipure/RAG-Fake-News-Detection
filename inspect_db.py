
import chromadb
from utils.config import CHROMA_PATH, COLLECTION_NAME

def inspect_knowledge_base():
    """連接到 ChromaDB 並顯示儲存的內容。"""
    print(f"Connecting to ChromaDB at: {CHROMA_PATH}")
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_collection(name=COLLECTION_NAME)
        print(f"Successfully connected to collection: '{COLLECTION_NAME}'")
    except Exception as e:
        print(f"Error connecting to ChromaDB: {e}")
        print("Please make sure you have run the indexing script (main_indexing.py) first.")
        return

    # 獲取集合中的所有項目
    # 注意：如果資料庫很大，這可能會輸出大量資訊
    results = collection.get()
    count = len(results['ids'])

    if count == 0:
        print("The knowledge base is empty.")
        return

    print(f"Found {count} entries in the knowledge base. Displaying content:")
    print("-" * 50)

    # 遍歷並印出每個項目的詳細資訊
    for i in range(count):
        doc_id = results['ids'][i]
        metadata = results['metadatas'][i]
        document = results['documents'][i]

        print(f"ID: {doc_id}")
        print(f"  Source: {metadata.get('source', 'N/A')}")
        print(f"  Title: {metadata.get('title', 'N/A')}")
        print(f"  URL: {metadata.get('url', 'N/A')}")
        print(f"  Status: {metadata.get('status', 'N/A')}") # 如果有儲存查核狀態
        print(f'''  Content Chunk: 
---
{document}
---''')
        print("-" * 50)

if __name__ == "__main__":
    inspect_knowledge_base()
