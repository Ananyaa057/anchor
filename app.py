"""
app.py - Streamlit Web UI for Anchor (Phase 1).

This is the presentation layer for Anchor.
It connects user input to the BM25 search engine implemented in `search.py`.

Phase 1 Scope:
- Loads runbooks from the 'runbooks/' folder.
- Keyword-based search using rank-bm25.
- Displays top 3 matching runbooks with relevance scores and full text.
"""

import streamlit as st
from search import BM25SearchEngine

# ---------------------------------------------------------
# 1. Page Configuration & Custom Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Anchor - Runbook Search",
    page_icon="⚓",
    layout="wide"
)

# Custom CSS to provide a clean, modern, and readable aesthetic
st.markdown("""
<style>
    /* Main container styling */
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .sub-title {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }

    /* Result Card Styling */
    .result-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .result-card:hover {
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
    }
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid #F1F5F9;
    }
    .card-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #0F172A;
        margin: 0;
    }
    .card-file {
        font-size: 0.85rem;
        color: #64748B;
        font-family: monospace;
        background-color: #F8FAFC;
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid #E2E8F0;
    }
    .badge-rank {
        display: inline-block;
        padding: 2px 10px;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 20px;
        margin-right: 8px;
    }
    .badge-rank-1 {
        background-color: #FEF3C7;
        color: #92400E;
        border: 1px solid #FDE68A;
    }
    .badge-rank-2 {
        background-color: #E0E7FF;
        color: #3730A3;
        border: 1px solid #C7D2FE;
    }
    .badge-rank-3 {
        background-color: #F1F5F9;
        color: #475569;
        border: 1px solid #CBD5E1;
    }
    .score-badge {
        background-color: #ECFDF5;
        color: #065F46;
        font-size: 0.85rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid #A7F3D0;
    }
    .content-box {
        background-color: #F8FAFC;
        border-radius: 6px;
        padding: 1rem;
        font-size: 0.92rem;
        line-height: 1.6;
        color: #334155;
        white-space: pre-wrap;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        border: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# 2. Search Engine Initialization (Cached for Performance)
# ---------------------------------------------------------
# Streamlit reruns the script on every user interaction.
# Using @st.cache_resource ensures we only scan and index the runbooks once,
# rather than re-reading files from disk on every keystroke.
@st.cache_resource
def get_search_engine() -> BM25SearchEngine:
    """Loads documents and builds the BM25 index."""
    return BM25SearchEngine(folder_path="runbooks")


# Load our search engine
engine = get_search_engine()


# ---------------------------------------------------------
# 3. Sidebar: Runbook Overview & Quick Suggestions
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚓ Anchor Runbooks")
    st.caption("Phase 1: Keyword-Based BM25 Retrieval")

    # Display total number of loaded documents
    total_docs = len(engine.documents)
    st.metric(label="Loaded Runbooks", value=total_docs)

    st.markdown("---")
    st.subheader("📚 Available Documents")
    for doc in engine.documents:
        st.write(f"- `{doc['filename']}`")

    st.markdown("---")
    st.subheader("💡 Try Example Queries")
    st.caption("Click any query to populate the search box:")

    # Quick example buttons to test keyword retrieval
    sample_queries = [
        "payment failure checkout error",
        "client not responding to emails",
        "database connection timeout",
        "deployment failed build error",
        "server down high cpu load",
        "website 502 bad gateway",
    ]

    for sample in sample_queries:
        if st.button(f"🔍 {sample}", key=f"sample_{sample}", use_container_width=True):
            st.session_state["search_query"] = sample
            st.rerun()


# ---------------------------------------------------------
# 4. Main Page Header
# ---------------------------------------------------------
st.markdown('<div class="main-title">⚓ Anchor — Runbook Search</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">'
    'Search through company runbooks using BM25 keyword matching to find incident resolution steps fast.'
    '</div>',
    unsafe_allow_html=True
)

# Initialize session state for query if not already present
if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""


# ---------------------------------------------------------
# 5. Search Input Box
# ---------------------------------------------------------
# Text input where the user describes the problem or question
query = st.text_input(
    label="Search runbooks by keywords or symptoms:",
    value=st.session_state["search_query"],
    placeholder="e.g. payment gateway failing, client silent, database connection...",
    key="search_input"
)

# Keep the session state in sync with user input
st.session_state["search_query"] = query


# ---------------------------------------------------------
# 6. Execute Search & Display Results
# ---------------------------------------------------------
if query.strip():
    # Perform BM25 keyword search requesting top 3 matches
    results = engine.search(query, top_k=3)

    st.markdown(f"### Results for: *\"{query}\"*")

    if not results:
        st.info("No matching runbooks found. Try different keywords.")
    else:
        # Check if the highest score is 0.0 (meaning no query words appeared in any document)
        top_score = results[0]["score"]
        if top_score == 0.0:
            st.warning("⚠️ None of the words matched any runbook directly. Showing default rankings:")

        # Loop through the top 3 results and render each one
        for rank, res in enumerate(results, start=1):
            rank_class = f"badge-rank-{min(rank, 3)}"

            st.markdown(f"""
            <div class="result-card">
                <div class="card-header">
                    <div>
                        <span class="badge-rank {rank_class}">Rank #{rank}</span>
                        <span class="card-title">{res['title']}</span>
                    </div>
                    <div>
                        <span class="card-file">{res['filename']}</span>
                        <span class="score-badge">BM25 Score: {res['score']:.2f}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Display the full matching runbook text clearly
            with st.expander(f"📄 View Full Runbook Content — {res['title']}", expanded=(rank == 1)):
                st.markdown(f'<div class="content-box">{res["content"]}</div>', unsafe_allow_html=True)

else:
    # Helpful guidance when no query has been entered yet
    st.info("👆 Enter a problem, symptom, or question in the search box above to find relevant runbooks.")
