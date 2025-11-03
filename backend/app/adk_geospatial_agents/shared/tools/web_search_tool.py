"""
Web Search Tool for DataConsultantAgent
"""

import asyncio
import warnings
from typing import List, Dict, Any, Optional

# Suppress RuntimeWarning from duckduckgo_search package rename
# Use more aggressive filtering
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", message=".*duckduckgo_search.*")

try:
    from ddgs import DDGS  # New package name
except ImportError:
    # Suppress warning during import
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        from duckduckgo_search import DDGS  # Fallback to old name

class WebSearchTool:
    """Web search tool using DuckDuckGo"""
    
    def __init__(self):
        self.max_results = 5  # Configurable number of results
        self.search_timeout = 10  # Timeout in seconds
    
    async def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search the web using DuckDuckGo
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: self.max_results)
        
        Returns:
            List of search results with title, url, and snippet
        """
        if max_results is None:
            max_results = self.max_results
        
        print(f"🔍 [WebSearchTool] Searching for: '{query}' (max_results: {max_results})")
        
        try:
            # Run DuckDuckGo search in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, 
                self._perform_search, 
                query, 
                max_results
            )
            
            print(f"🔍 [WebSearchTool] Found {len(results)} results")
            return results
            
        except Exception as e:
            print(f"❌ [WebSearchTool] Search error: {str(e)}")
            return []
    
    def _perform_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Perform the actual search (runs in thread pool)"""
        try:
            # Suppress warnings during DDGS usage
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with DDGS() as ddgs:
                    # Get text search results
                    results = list(ddgs.text(
                        query, 
                        max_results=max_results,
                        safesearch='moderate'
                    ))
                
                # Format results
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", ""),
                        "source": "DuckDuckGo"
                    })
                
                return formatted_results
                
        except Exception as e:
            print(f"❌ [WebSearchTool] DuckDuckGo search error: {str(e)}")
            return []
    
    async def search_data_analysis_topic(self, topic: str) -> List[Dict[str, Any]]:
        """
        Search for data analysis related topics with optimized queries
        
        Args:
            topic: Data analysis topic to search for
        
        Returns:
            List of search results
        """
        # Optimize query for data analysis topics
        optimized_query = f"{topic} data analysis best practices tutorial"
        
        return await self.search(optimized_query)
    
    def format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results into a readable string
        
        Args:
            results: List of search results
        
        Returns:
            Formatted string with results
        """
        if not results:
            return "No search results found."
        
        formatted_text = "**Search Results:**\n\n"
        
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            snippet = result.get("snippet", "No description available")
            
            # Truncate snippet if too long
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."
            
            formatted_text += f"{i}. **{title}**\n"
            formatted_text += f"   {snippet}\n"
            formatted_text += f"   Source: {url}\n\n"
        
        return formatted_text
    
    def get_source_links(self, results: List[Dict[str, Any]]) -> str:
        """
        Get formatted source links from search results
        
        Args:
            results: List of search results
        
        Returns:
            Formatted string with source links
        """
        if not results:
            return ""
        
        links_text = "**Sources:**\n"
        for i, result in enumerate(results, 1):
            title = result.get("title", f"Source {i}")
            url = result.get("url", "")
            links_text += f"{i}. [{title}]({url})\n"
        
        return links_text

# Global instance
web_search_tool = WebSearchTool()
