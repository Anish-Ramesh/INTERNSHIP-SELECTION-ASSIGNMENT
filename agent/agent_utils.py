import os
import json
import re
from tools.search_docs import tokenize

# Paths for cache storage
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
RESPONSE_CACHE_PATH = os.path.join(CACHE_DIR, "response_cache.json")
EVAL_CACHE_PATH = os.path.join(CACHE_DIR, "eval_cache.json")

# Advanced Deduplication Stop Words
AGENT_STOP_WORDS = {
    "movie", "movies", "film", "films", "search", "find", "get", "show", "series", "info", 
    "information", "details", "data", "list", "identify", "tell", "check", "looking"
}

def clean_final_answer(text: str) -> str:
    """Strip internal reasoning blocks (STRATEGIC BREAKDOWN, THOUGHT, PLAN, etc.) from the final response."""
    # Remove STRATEGIC BREAKDOWN:, THOUGHT:, PLAN:
    text = re.sub(r"(?i)STRATEGIC BREAKDOWN:.*?(?=THOUGHT:|PLAN:|\[AGENT RESPONSE\]|$)", "", text, flags=re.DOTALL)
    text = re.sub(r"(?i)THOUGHT:.*?(?=PLAN:|\[AGENT RESPONSE\]|$)", "", text, flags=re.DOTALL)
    text = re.sub(r"(?i)PLAN:.*?(?=\[AGENT RESPONSE\]|$)", "", text, flags=re.DOTALL)
    return text.strip()

def normalize_output(result: any, max_len: int = 2000) -> str:
    """Clean and truncate tool outputs for the context layer."""
    clean = str(result).strip()
    if len(clean) > max_len:
        return clean[:max_len] + "\n...[truncated for context]"
    return clean

def extract_citations(text: str) -> list:
    """Extract granular citation identifiers from the final answer text."""
    patterns = [
        r"\[Source: [^\]]+, Page: \d+\]",
        r"\[Web Source \d+\]",
        r"\[Table: movies, Row: [^\]]+\]"
    ]
    citations = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        citations.extend(matches)
    # Deduplicate while preserving order if possible (set is fine here)
    return list(set(citations))

def load_cache(cache_path=None):
    if cache_path is None:
        cache_path = RESPONSE_CACHE_PATH
        
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache, cache_path=None, enable_rollover=False):
    """
    Saves cache to disk. If enable_rollover is True and count > 1000, 
    removes 100 oldest entries (FIFO).
    """
    if cache_path is None:
        cache_path = RESPONSE_CACHE_PATH

    if enable_rollover and len(cache) > 1000:
        # Remove oldest 100 (dict preserves insertion order since 3.7)
        keys_to_remove = list(cache.keys())[:100]
        for k in keys_to_remove:
            del cache[k]
        print(f">>> [CACHE OVERFLOW] Removed 100 oldest items. Current size: {len(cache)}")

    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=4)
    except:
        pass
