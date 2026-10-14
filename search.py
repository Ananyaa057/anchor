"""
search.py - Document loading and BM25 search logic for Anchor (Phase 1).

This module handles:
1. Loading all runbook text files from the "runbooks/" directory.
2. Tokenizing documents and queries (converting text into lists of lowercase words).
3. Indexing documents with BM25 (BM25Okapi from rank-bm25).
4. Querying the index and ranking results by relevance score.
"""

import os
import re
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi


def tokenize(text: str) -> List[str]:
    """
    Convert raw text into a list of cleaned, lowercase word tokens.

    Why this is needed:
    BM25 compares word occurrences between queries and documents.
    By converting to lowercase and stripping punctuation, words like
    "Server", "server!", and "server" are treated as the same token.

    Example:
        "Server is down!" -> ["server", "is", "down"]
    """
    # Find all alphanumeric sequences and convert to lowercase.
    # This splits words cleanly on whitespace, punctuation, and underscores.
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def load_runbooks(folder_path: str = "runbooks") -> List[Dict[str, Any]]:
    """
    Scan the runbooks folder and load every .txt file as a document.

    Returns:
        A list of dictionaries, where each dictionary represents one runbook:
        {
            "filename": "server_down.txt",
            "title": "Server Down",
            "content": "RUNBOOK: Server Down\n..."
        }
    """
    documents = []

    # Verify that the runbooks directory exists
    if not os.path.isdir(folder_path):
        return documents

    # Iterate through all files in the given directory
    for filename in sorted(os.listdir(folder_path)):
        # We only care about .txt files
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Attempt to extract a clean title from the first line (e.g. "RUNBOOK: Server Down")
            # If not formatted that way, fall back to cleaning up the filename
            title = filename.replace(".txt", "").replace("_", " ").title()
            first_line = content.strip().split("\n")[0] if content.strip() else ""
            if first_line.upper().startswith("RUNBOOK:"):
                title = first_line.split(":", 1)[1].strip()

            documents.append({
                "filename": filename,
                "title": title,
                "content": content
            })

    return documents


class BM25SearchEngine:
    """
    Encapsulates BM25 keyword search over a collection of runbook documents.
    """

    def __init__(self, folder_path: str = "runbooks"):
        """
        Initialize the search engine:
        1. Load all runbook documents from the folder.
        2. Tokenize each document's text.
        3. Build the BM25 index.
        """
        self.folder_path = folder_path
        self.documents = load_runbooks(folder_path)

        # Tokenize each document's full content for BM25 indexing
        self.tokenized_corpus = [
            tokenize(doc["content"]) for doc in self.documents
        ]

        # Initialize the BM25Okapi model with the tokenized corpus
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        else:
            self.bm25 = None

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search the runbooks for a user query and return top_k matching results.

        Steps:
        1. Tokenize the incoming query string.
        2. Calculate BM25 relevance scores for all documents.
        3. Sort documents by score in descending order (highest score first).
        4. Return top_k results.
        """
        # If no documents exist or the query is empty/whitespace, return empty list
        if not self.bm25 or not query.strip():
            return []

        # 1. Break the user query into lowercase tokens
        tokenized_query = tokenize(query)
        if not tokenized_query:
            return []

        # 2. Get BM25 relevance score for each document in the corpus
        # get_scores() returns a list/array of float scores matching the order of self.documents
        scores = self.bm25.get_scores(tokenized_query)

        # 3. Pair each document with its corresponding score
        results = []
        for doc, score in zip(self.documents, scores):
            results.append({
                "filename": doc["filename"],
                "title": doc["title"],
                "content": doc["content"],
                "score": float(score)
            })

        # 4. Sort results so the highest score comes first
        results.sort(key=lambda x: x["score"], reverse=True)

        # 5. Return only the top_k ranked documents
        return results[:top_k]
