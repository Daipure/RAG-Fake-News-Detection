# ui/app.py
import streamlit as st
import sys
import os

# 將專案根目錄加入 sys.path，以便匯入其他模組
current_dir = os.path.dirname(__file__)
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(root_dir)

from reasoning.fact_checker import FactChecker

# --- 頁面設定 ---
st.set_page_config(page_title="RAG 假新聞偵測系統", layout="wide", initial_sidebar_state="expanded")

# --- 側邊欄 ---
with st.sidebar:
    st.title("關於本系統")
    st.info(
        """本系統使用 RAG (檢索增強生成) 技術，結合大型語言模型 (LLM) 與本地知識庫，
        提供對輸入文本的事實查核功能。"""
    )
    st.markdown("**技術棧:**")
    st.markdown("- Streamlit (前端介面)")
    st.markdown("- Ollama (大型語言模型服務)")
    st.markdown("- ChromaDB (向量儲存)")
    st.markdown("- BM25 (關鍵字檢索)")
    st.markdown("---")
    st.write("由 Daipure 開發")

# --- 主頁面 ---
st.title("🔍 RAG 假新聞偵測系統")
st.markdown("#### 結合檢索增強生成與大型語言模型，提供即時、有依據的事實查核")

# --- 頂部結論區塊的佔位符 ---
final_verdict_placeholder = st.empty()

# --- 初始化 ---
@st.cache_resource
def load_fact_checker():
    """快取 FactChecker 物件，避免每次互動都重新載入模型。"""
    return FactChecker()

fact_checker = load_fact_checker()

# --- 輸入區塊 ---
st.subheader("請輸入您想查核的內容")
user_query = st.text_area("輸入文本：", "", height=150, placeholder="例如：昨晚高雄因大雷雨停電，導致數千戶居民無電可用。")

if st.button("開始查核", type="primary", use_container_width=True):
    # 清空上一次的頂部結論
    final_verdict_placeholder.empty()

    if not user_query.strip():
        st.warning("請輸入內容後再點擊查核。")
    elif not fact_checker.collection:
        st.error("知識庫尚未建立或載入失敗，請先執行 `main_indexing.py`。")
    else:
        with st.spinner("系統正在分析中，請稍候... (這可能需要一點時間)"):
            results = fact_checker.check(user_query)

        st.success("分析完成！")
        
        # --- 結果顯示區塊 ---
        if results and results.get("results_per_claim"):
            # --- FINAL OVERALL VERDICT (顯示在頂部) ---
            all_verdicts = [res['final_verdict'] for res in results["results_per_claim"]]
            with final_verdict_placeholder.container():
                st.header("📝 總結報告")
                with st.container(border=True):
                    if "False" in all_verdicts:
                        st.error("## ‼️‼️ 這是假新聞 ‼️‼️")
                    elif all(v == "True" for v in all_verdicts):
                        st.success("## ✅✅ 這是真新聞 ✅✅")
                    else:
                        st.warning("## ❔❔ 中立/資訊不足 ❔❔")
                st.markdown("--- ") # 在總結報告下方加上分隔線

            # --- 詳細分析 ---
            st.markdown(f"**原始查詢:** `{results.get('query')}`")
            st.markdown(f"**優化後查詢:** `{results.get('rewritten_query')}`")
            st.markdown("--- ")

            for i, claim_result in enumerate(results["results_per_claim"]):
                st.subheader(f"查核主張 {i+1}: `{claim_result['claim']}`")
                
                col1, col2 = st.columns([1, 2.5])

                with col1:
                    verdict = claim_result['final_verdict']
                    if verdict == "True":
                        st.success("#### ✅ 真實 (True)")
                    elif verdict == "False":
                        st.error("#### ❌ 錯誤 (False)")
                    elif verdict == "Abstain":
                        st.warning("#### ⚠️ 放棄判斷 (Abstain)")
                    else:
                        st.info("#### ❔ 中立/資訊不足 (Neutral)")
                    
                    st.write("**判斷理由:**")
                    st.info(f"{claim_result['reasoning']}")

                with col2:
                    st.write("**相關證據比對:**")
                    alignments = claim_result.get("evidence_alignments", [])
                    if not alignments:
                        st.write("沒有找到可用於比對的證據。")
                    else:
                        for align in alignments:
                            evidence = align['evidence']
                            with st.container(border=True):
                                label = align.get('label', 'N/A')
                                if label == "支持":
                                    st.markdown(f"**比對結果: <span style='color:green; font-weight:bold;'>{label}</span>**", unsafe_allow_html=True)
                                elif label == "矛盾":
                                    st.markdown(f"**比對結果: <span style='color:red; font-weight:bold;'>{label}</span>**", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"**比對結果: <span style='color:orange; font-weight:bold;'>{label}</span>**", unsafe_allow_html=True)

                                st.markdown(f"**來源:** {evidence['metadata'].get('source', 'N/A')} | **發布日期:** {evidence['metadata'].get('publication_date', 'N/A')}")
                                st.markdown(f"**標題:** [{evidence['metadata'].get('title', 'N/A')}]({evidence['metadata'].get('url', '#')})", unsafe_allow_html=True)
                                
                                with st.expander("查看證據原文與 LLM 分析"):
                                    st.code(evidence['content'], language=None)
                                    st.write("**LLM 分析 JSON:**")
                                    st.json(align)
                            st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.error("處理時發生錯誤，無法取得結果。")