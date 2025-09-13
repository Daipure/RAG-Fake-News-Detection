
# utils/config.py
import os

# Project Root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# LLM and Embedding Models
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "gemma3:4b" # 或者 gemma:7b, mistral, etc.
EMBEDDING_MODEL = "shibing624/text2vec-base-chinese" 


# Vector Database
CHROMA_PATH = os.path.join(ROOT_DIR, "chroma_db")
COLLECTION_NAME = "fact_checking_collection"

# Data Paths
DATA_DIR = os.path.join(ROOT_DIR, "data")
PROCESSED_DATA_PATH = os.path.join(DATA_DIR, "processed_articles.json")

# Text Chunking
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# Fact-Checking Reasoning
# 用於讓 LLM 判斷 "主張" 與 "證據" 之間的關係
FACT_ALIGNMENT_PROMPT_TEMPLATE = """
你是一位事實查核專家。你的任務是根據一段「證據」和它的「發布日期」，來判斷一個「主張」的真偽。
根據所提供的證據，你必須將主張歸類為以下三種類型之一：「支持」、「矛盾」或「中立」。

- 「支持」(Entailment): 證據直接支持或證明了該主張。
- 「矛盾」(Contradiction): 證據直接反駁或否定了該主張。
- 「中立」(Neutral): 證據與主張相關，但未提供足夠資訊來支持或反駁它。

在做決定時，請務必考慮證據的「時效性」。一篇過時的文章可能與近期發生的事件無關。

你必須以 JSON 格式回應，包含三個欄位：「label」、「reasoning」和「confidence_score」。
- 「label」: 你的分類結果 (「支持」、「矛盾」或「中立」)。
- 「reasoning」: 一句簡短的解釋，說明你為何如此判斷。如果證據的發布日期是判斷的關鍵，請在理由中提及。
- 「confidence_score」: 一個介於 0.0 和 1.0 之間的浮點數，代表你的信心指數。

資料如下：
主張 (Claim): {claim}
證據 (Evidence): {evidence}
證據發布日期 (Evidence Publication Date): {publication_date}

你的 JSON 回應：
"""

# 用於從使用者輸入中抽取核心主張
CLAIM_EXTRACTION_PROMPT_TEMPLATE = """
你是一位資訊分析專家。你的任務是從使用者輸入的文本中，提取出核心、可供查證的「主張」。
一個「主張」應該是一個可以被獨立驗證的簡單陳述句。
請將複雜的句子拆解成多個原子性的主張。

例如，如果輸入是「昨天，台北因颱風發生大規模停電，影響了數千戶家庭。」，你應該提取出：
1. 台北昨天發生了大規模停電。
2. 停電是由颱風引起的。
3. 數千戶家庭受到了停電的影響。

現在，請分析以下文本，並以 JSON 物件格式返回結果。JSON 物件應包含一個鍵「claims」，其值為一個包含所有主張字串的列表。
輸入文本: {user_input}

你的 JSON 回應：
"""

# 用於查詢理解 (Query Understanding)
QUERY_REWRITING_PROMPT_TEMPLATE = """
你是一位查詢優化專家。你的任務是將使用者的輸入改寫成一個清晰、簡潔、獨立的問題，以優化事實查核系統的檢索結果。
改寫後的查詢應該是一個中立、客觀的問題。

- 如果輸入本身已經是一個好的查詢，直接回傳即可。
- 如果輸入是口語化的、包含代名詞或語意模糊，請將其改寫成一個具體的、自身完整的問題。
- 輸出必須是一個單一的問題。

使用者輸入: "{user_input}"

改寫後的查詢:
"""
