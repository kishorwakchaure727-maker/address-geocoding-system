"""
Fully Agentic Mode - AI Verification Engine.
Uses Google's Gemini to verify address accuracy via web search.
"""
import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from typing import Dict, Optional, Tuple, List
import json
import re

from . import config

class AgenticVerifier:
    """Uses LLM to verify addresses found by geocoder."""
    
    def __init__(self, api_key: str = None):
        """Initialize the verifier with Gemini API key."""
        self.api_key = api_key or config.GOOGLE_AI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    def verify(self, company: str, geocoded_address: str) -> Dict:
        """
        Verify the geocoded address against web search results.
        
        Args:
            company: Company name
            geocoded_address: Address found by geocoder
            
        Returns:
            Dict with verification results
        """
        if not self.model:
            return {
                "status": "skipped",
                "message": "AI API Key not configured",
                "confidence": 0,
                "source_url": ""
            }

        # 1. Search for company website/address
        search_results = self._search_web(f"{company} official website address")
        
        # 2. Extract potential info
        context = self._extract_context(search_results)
        
        # 3. Use LLM to verify
        prompt = f"""
        Company: {company}
        Address Found by Geocoder: {geocoded_address}
        
        Web Search Context:
        {context}
        
        Tasks:
        1. Find the official website or most reliable source for the company's address.
        2. Extract the address from the context.
        3. Compare the AI-found address with the Geocoded address.
        4. Rate your confidence (0-1) that the Geocoded address is correct.
        
        Return a JSON object:
        {{
            "found_address": "string",
            "source_url": "string",
            "is_match": boolean,
            "confidence": float,
            "explanation": "string"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Find JSON in response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "status": "verified" if result.get("confidence", 0) > 0.7 else "uncertain",
                    "message": result.get("explanation", ""),
                    "confidence": result.get("confidence", 0),
                    "source_url": result.get("source_url", ""),
                    "ai_address": result.get("found_address", "")
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to parse AI response",
                    "confidence": 0,
                    "source_url": ""
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"AI Verification error: {str(e)}",
                "confidence": 0,
                "source_url": ""
            }

    def _search_web(self, query: str) -> List[Dict]:
        """Perform a simple web search using Google Search (via scraping/url)."""
        # This is a simplified search logic as we don't have a dedicated Search API key requirement yet.
        # We'll use a search URL and extract snippets.
        try:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            for g in soup.find_all('div', class_='g'):
                anchors = g.find_all('a')
                if anchors:
                    link = anchors[0]['href']
                    title = g.find('h3').text if g.find('h3') else ""
                    snippet = g.find('div', class_='VwiC3b').text if g.find('div', class_='VwiC3b') else ""
                    results.append({"title": title, "link": link, "snippet": snippet})
            
            return results[:3] # Top 3
        except:
            return []

    def _extract_context(self, results: List[Dict]) -> str:
        """Convert results list to a string context."""
        context = ""
        for res in results:
            context += f"Source: {res['link']}\nSnippet: {res['snippet']}\n\n"
        return context
