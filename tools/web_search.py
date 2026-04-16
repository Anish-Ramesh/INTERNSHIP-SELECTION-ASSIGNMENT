import os
import requests
import json
from dotenv import load_dotenv

class WebSearchTool:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.url = "https://api.tavily.com/search"

    def search(self, query: str, max_results: int = 3) -> str:
        """
        Use this tool to handle real-time information retrieval from the internet.
        It is ideal for identifying recent awards, director updates, or current events
        that are not available in the local structured or unstructured databases.
        
        DO NOT use this tool for qualitative review searches or box-office aggregates
        unless explicitly required by a lack of local data.
        
        Args:
            query (str): A concise search string (preferably under 10 words).
            
        Returns:
            str: The top search results consisting of snippet, URL, and published date.
        """
        if not self.api_key:
            return "Error: TAVILY_API_KEY is not set in the environment. Cannot perform web search."
            
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "include_domains": [],
            "exclude_domains": [],
            "search_depth": "basic",
        }
        
        try:
            response = requests.post(self.url, json=payload, timeout=10)
            if response.status_code != 200:
                return f"Error executing web search: {response.text}"
                
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                return "No real-time results found for the query."
                
            formatted_results = []
            # Added enumerate to give each source a distinct number
            for i, res in enumerate(results, 1):
                title = res.get("title", "No Title")
                url = res.get("url", "No URL")
                snippet = res.get("content", "No content")
                pub_date = res.get("published_date", "Date not available") 
                
                # Structured cleanly for the LLM to read and cite
                source_text = (
                    f"[Web Source {i}]\n"
                    f"Title: {title}\n"
                    f"URL: {url}\n"
                    f"Date: {pub_date}\n"
                    f"Snippet: {snippet}"
                )
                formatted_results.append(source_text)
                
            return "\n\n---\n\n".join(formatted_results)
            
        except Exception as e:
            return f"Error executing web search: {str(e)}"

# Convenience wrapper
_web_search_tool_instance = None
def web_search(query: str) -> str:
    """
    Real-time web search for current events and updates.
    Use this to answer questions about recent awards, live web updates, or information not present in the local reviews or database.
    Query should be short (under 10 words).
    IMPORTANT: When using information from this tool, you MUST cite the specific URL and Date in your final answer.
    """
    global _web_search_tool_instance
    if _web_search_tool_instance is None:
        _web_search_tool_instance = WebSearchTool()
    return _web_search_tool_instance.search(query)