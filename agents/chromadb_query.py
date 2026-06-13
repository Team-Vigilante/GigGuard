# Agent 2 — ChromaDB Query Logic
# Owner: Person 2 (AI Agents + Prompt Engineering)
# Used by: researcher_node() in agents/researcher_node.py

import chromadb
from chromadb.utils import embedding_functions
import os


# Relevance threshold — chunks below this score are ignored
RELEVANCE_THRESHOLD = 0.4


def get_chroma_client() -> chromadb.Collection:
    """
    Initialize ChromaDB client and return the legal knowledge
    base collection.
    
    Returns:
        ChromaDB collection object
    """
    client = chromadb.PersistentClient(path="./gigguard.db")
    
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    
    collection = client.get_or_create_collection(
        name="legal_knowledge_base",
        embedding_function=embedding_fn
    )
    
    return collection


def query_knowledge_base(
    case_facts: str,
    n_results: int = 5
) -> list:
    """
    Query ChromaDB for legal chunks relevant to the case facts.
    
    Args:
        case_facts: A string describing the worker's case.
                   Example: "Swiggy deactivated account without 
                   notice, withheld earnings of 3200 rupees"
        n_results:  Number of results to return (default 5)
    
    Returns:
        List of relevant chunks, each containing:
        {
            "id": str,
            "text": str,
            "source": str,
            "section": str,
            "relevance_score": float
        }
        Returns empty list if no relevant chunks found.
    """
    
    # Guard — empty input
    if not case_facts or not case_facts.strip():
        print("[ChromaDB] Empty case facts received — returning []")
        return []
    
    try:
        collection = get_chroma_client()
        
        # Guard — empty collection
        if collection.count() == 0:
            print("[ChromaDB] Collection is empty — returning []")
            return []
        
        # Query ChromaDB
        results = collection.query(
            query_texts=[case_facts],
            n_results=min(n_results, collection.count()),
            include=["documents", "metadatas", "distances"]
        )
        
        # Parse results
        chunks = []
        
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]
        
        for doc, meta, distance in zip(
            documents, metadatas, distances
        ):
            # Convert distance to relevance score
            # ChromaDB returns distance — lower = more similar
            # We convert to score — higher = more relevant
            relevance_score = 1 - distance
            
            # Filter by threshold
            if relevance_score < RELEVANCE_THRESHOLD:
                print(
                    f"[ChromaDB] Chunk below threshold "
                    f"({relevance_score:.2f}) — skipped"
                )
                continue
            
            chunks.append({
                "id": meta.get("id", "unknown"),
                "text": doc,
                "source": meta.get("source", "unknown"),
                "section": meta.get("section", "unknown"),
                "relevance_score": round(relevance_score, 3)
            })
        
        print(f"[ChromaDB] Returned {len(chunks)} relevant chunks")
        return chunks
    
    except Exception as e:
        print(f"[ChromaDB] Query failed: {e}")
        return []


def build_case_facts_string(parsed_data: dict) -> str:
    """
    Convert parsed_data from GigGuardState into a plain English
    string for ChromaDB semantic search.
    
    Args:
        parsed_data: The parsed_data dict from GigGuardState
    
    Returns:
        A plain English string describing the case
    
    Example output:
        "Swiggy account deactivation. No notice provided. 
         No appeal offered. Earnings withheld: 3200 INR. 
         Reason given: NO_REASON_PROVIDED"
    """
    
    parts = []
    
    if parsed_data.get("platform"):
        parts.append(parsed_data["platform"])
    
    if parsed_data.get("event_type"):
        event = parsed_data["event_type"].replace("_", " ").lower()
        parts.append(event)
    
    if parsed_data.get("notice_provided") is False:
        parts.append("no notice provided")
    elif parsed_data.get("notice_provided") is True:
        parts.append("notice was provided")
    
    if parsed_data.get("appeal_offered") is False:
        parts.append("no appeal offered")
    elif parsed_data.get("appeal_offered") is True:
        parts.append("appeal was offered")
    
    if parsed_data.get("earnings_withheld"):
        parts.append(
            f"earnings withheld: "
            f"{parsed_data['earnings_withheld']} INR"
        )
    
    if parsed_data.get("reason"):
        parts.append(f"reason given: {parsed_data['reason']}")
    
    return ". ".join(parts)