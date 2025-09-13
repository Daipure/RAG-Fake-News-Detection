
# reasoning/fact_checker.py
import json
import ollama
import chromadb
from langchain_community.embeddings import SentenceTransformerEmbeddings
from rank_bm25 import BM25Okapi

from utils.config import (
    OLLAMA_MODEL,
    EMBEDDING_MODEL,
    CHROMA_PATH,
    COLLECTION_NAME,
    FACT_ALIGNMENT_PROMPT_TEMPLATE,
    CLAIM_EXTRACTION_PROMPT_TEMPLATE,
    QUERY_REWRITING_PROMPT_TEMPLATE
)

class FactChecker:
    """整合了檢索和生成，進行事實查核的核心類別。"""
    def __init__(self):
        print("Initializing FactChecker...")
        self.ollama_client = ollama.Client()
        self.embedding_function = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)
        
        self.db_client = None
        self.collection = None
        self.bm25_index = None
        self.chunk_corpus = []

        try:
            self.db_client = chromadb.PersistentClient(path=CHROMA_PATH)
            self.collection = self.db_client.get_collection(name=COLLECTION_NAME)
            print("Successfully connected to ChromaDB.")
            self._initialize_bm25_from_chroma()
        except Exception as e:
            print(f"Error connecting to ChromaDB or initializing BM25: {e}")
            print(f"Please make sure you have run the indexing script first.")

    def _initialize_bm25_from_chroma(self):
        if not self.collection:
            return
        print("Initializing BM25 index from ChromaDB documents...")
        try:
            all_docs = self.collection.get(include=["documents", "metadatas"])
            self.chunk_corpus = [
                {"id": all_docs['ids'][i], "content": doc, "metadata": all_docs['metadatas'][i]}
                for i, doc in enumerate(all_docs['documents'])
            ]
            tokenized_corpus = [doc['content'].split() for doc in self.chunk_corpus]
            self.bm25_index = BM25Okapi(tokenized_corpus)
            print(f"Successfully initialized BM25 index with {len(self.chunk_corpus)} documents.")
        except Exception as e:
            print(f"Error initializing BM25 index: {e}")

    def _call_llm(self, prompt: str, json_format: bool = True) -> dict | str:
        """呼叫本地 Ollama 模型。"""
        try:
            response = self.ollama_client.chat(
                model=OLLAMA_MODEL,
                messages=[{'role': 'user', 'content': prompt}],
                format='json' if json_format else ''
            )
            content = response['message']['content']
            if json_format:
                return json.loads(content)
            else:
                return content
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return None

    def rewrite_query(self, query: str) -> str:
        """為更好的檢索重寫使用者查詢。"""
        print(f"Original query: {query}")
        prompt = QUERY_REWRITING_PROMPT_TEMPLATE.format(user_input=query)
        
        rewritten_query = self._call_llm(prompt, json_format=False)
        
        if rewritten_query and rewritten_query.strip():
            rewritten_query = rewritten_query.strip()
            print(f"Rewritten query: {rewritten_query}")
            return rewritten_query
        else:
            print("Query rewriting failed. Using original query.")
            return query

    def extract_claims(self, query: str) -> list[str]:
        """使用 LLM 從使用者輸入中抽取核心主張。"""
        print(f"Extracting claims from: {query}")
        prompt = CLAIM_EXTRACTION_PROMPT_TEMPLATE.format(user_input=query)
        response_json = self._call_llm(prompt)
        
        if response_json and 'claims' in response_json and isinstance(response_json['claims'], list):
            claims = response_json['claims']
            print(f"Extracted claims: {claims}")
            return claims
        else:
            print("Failed to extract claims, using the original query as a single claim.")
            return [query]

    def _rerank_with_rrf(self, results_list: list[list[dict]], rrf_k: int = 60) -> list[dict]:
        """使用倒數排序融合 (Reciprocal Rank Fusion) 重新排序搜尋結果。"""
        scores = {}
        for results in results_list:
            for rank, doc in enumerate(results):
                doc_id = doc['id']
                if doc_id not in scores:
                    scores[doc_id] = 0
                scores[doc_id] += 1 / (rrf_k + rank + 1)

        sorted_doc_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        all_docs_map = {}
        for results in results_list:
            for doc in results:
                if doc['id'] not in all_docs_map:
                    all_docs_map[doc['id']] = doc

        return [all_docs_map[doc_id] for doc_id in sorted_doc_ids]

    def retrieve_evidence(self, claim: str, k: int = 5) -> list[dict]:
        """執行混合搜尋 (Vector + BM25) 以檢索 top-k 相關證據。"""
        if not self.collection or not self.bm25_index:
            print("Search components not initialized.")
            return []
            
        print(f"Performing hybrid search for claim: '{claim}'")

        claim_embedding = self.embedding_function.embed_query(claim)
        vector_results_raw = self.collection.query(
            query_embeddings=[claim_embedding],
            n_results=k,
            include=["metadatas", "documents"]
        )
        
        vector_results = []
        if vector_results_raw and vector_results_raw['ids'][0]:
            for i, doc_id in enumerate(vector_results_raw['ids'][0]):
                vector_results.append({
                    "id": doc_id,
                    "content": vector_results_raw['documents'][0][i],
                    "metadata": vector_results_raw['metadatas'][0][i]
                })

        tokenized_query = claim.split()
        bm25_scores = self.bm25_index.get_scores(tokenized_query)
        
        top_n_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:k]
        bm25_results = [self.chunk_corpus[i] for i in top_n_indices if bm25_scores[i] > 0]

        if not vector_results and not bm25_results:
            print("No evidence found from any search method.")
            return []
        
        reranked_results = self._rerank_with_rrf([vector_results, bm25_results])
        
        final_results = reranked_results[:k]
        print(f"Retrieved {len(final_results)} pieces of evidence after reranking.")
        return final_results

    def align_claim_with_evidence(self, claim: str, evidence: dict) -> dict:
        """使用 LLM 判斷單一主張與單一證據之間的關係。"""
        publication_date = evidence.get('metadata', {}).get('publication_date', 'N/A')
        prompt = FACT_ALIGNMENT_PROMPT_TEMPLATE.format(
            claim=claim, 
            evidence=evidence['content'],
            publication_date=publication_date
        )
        return self._call_llm(prompt)

    def check(self, query: str) -> dict:
        """執行完整的事實查核流程。"""
        if not self.collection:
            return {"error": "Knowledge base not available."}

        rewritten_query = self.rewrite_query(query)
        claims = self.extract_claims(rewritten_query)
        final_results = {"query": query, "rewritten_query": rewritten_query, "results_per_claim": []}

        for claim in claims:
            evidence_list = self.retrieve_evidence(claim)
            if not evidence_list:
                claim_result = {
                    "claim": claim,
                    "final_verdict": "Abstain",
                    "reasoning": "Could not find any relevant evidence in the knowledge base.",
                    "evidence": []
                }
                final_results["results_per_claim"].append(claim_result)
                continue

            alignments = []
            for evidence in evidence_list:
                alignment = self.align_claim_with_evidence(claim, evidence)
                if alignment:
                    alignment['evidence'] = evidence
                    alignments.append(alignment)
            
            final_verdict = "Neutral"
            final_reasoning = "證據與主張相關，但無法得出明確結論。"
            contradictions = [a for a in alignments if a.get('label') == '矛盾']
            entailments = [a for a in alignments if a.get('label') == '支持']

            if contradictions:
                final_verdict = "False"
                final_reasoning = contradictions[0]['reasoning']
            elif entailments:
                final_verdict = "True"
                final_reasoning = entailments[0]['reasoning']

            claim_result = {
                "claim": claim,
                "final_verdict": final_verdict,
                "reasoning": final_reasoning,
                "evidence_alignments": alignments
            }
            final_results["results_per_claim"].append(claim_result)

        return final_results
