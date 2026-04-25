from azure.ai.inference.models import (
    ChatCompletionsToolDefinition, 
    FunctionDefinition
)
from tools.search_docs import search_docs
from tools.query_data import query_data
from tools.web_search import web_search

# Strict Tool Definitions reflecting exactly our guardrails from Phase 1
TOOLS = [
     ChatCompletionsToolDefinition(
         function=FunctionDefinition(
             name="search_docs",
             description="Semantic search over unstructured documents (movie reviews). Use this ONLY for movies confirmed to be in the [LOCAL CORPUS INVENTORY]. DO NOT use for numerical data.",
             parameters={
                 "type": "object",
                 "properties": {
                     "query": {
                         "type": "string",
                         "description": "Natural language query string including movie title."
                     }
                 },
                 "required": ["query"]
             }
         )
     ),
     ChatCompletionsToolDefinition(
         function=FunctionDefinition(
             name="query_data",
             description="Query the structured financial / stats table for movies. The table contains the following columns: [title, year, genre, budget, opening_weekend, worldwide_gross, rotten_tomatoes_score]. Select ONLY necessary columns to avoid context bloating.",
             parameters={
                 "type": "object",
                 "properties": {
                     "sql_query": {
                         "type": "string",
                         "description": "A valid read-only SQLite query to run against the 'movies' table."
                     }
                 },
                 "required": ["sql_query"]
             }
         )
     ),
     ChatCompletionsToolDefinition(
         function=FunctionDefinition(
             name="web_search",
             description="Search the live web for recent information or as a fallback if local docs/SQL are insufficient. Limit to 2 calls per query.",
             parameters={
                 "type": "object",
                 "properties": {
                     "query": {
                         "type": "string",
                         "description": "A short search query string (under 10 words)."
                     }
                 },
                 "required": ["query"]
             }
         )
     )
]

TOOL_MAP = {
    "search_docs": search_docs,
    "query_data": query_data,
    "web_search": web_search
}
