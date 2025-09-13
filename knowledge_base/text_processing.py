
# knowledge_base/text_processing.py
import re

def clean_text(text: str) -> str:
    """簡單的文本清理函式。"""
    text = re.sub(r'\s+', ' ', text) # 替換多餘的空白字元
    text = text.strip()
    return text

def preprocess_documents(documents: list[dict]) -> list[dict]:
    """對整批文件進行預處理。"""
    for doc in documents:
        if 'content' in doc and isinstance(doc['content'], str):
            doc['content'] = clean_text(doc['content'])
    return documents
