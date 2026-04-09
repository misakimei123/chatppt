from __future__ import annotations

import hashlib
import logging
from typing import Any

from pydantic import BaseModel

from chatppt.app.domain.models.clarified_spec import ClarifiedSpec
from chatppt.app.domain.models.evidence_pack import (
    EvidenceFact,
    EvidencePack,
    EvidenceSource,
    EvidenceSuggestion,
)
from chatppt.app.infra.llm_provider import LLMProvider

logger = logging.getLogger(__name__)


class SourceDocument(BaseModel):
    title: str
    uri: str
    content: str
    source_type: str = "user_upload"


class SearchResult(BaseModel):
    """Represents a single search result from web search."""
    title: str
    url: str
    snippet: str
    source: str = "web_search"


class EvidenceBuilder:
    """
    Enhanced EvidenceBuilder with support for:
    1. Web search integration (via external API)
    2. Document parsing and RAG retrieval
    3. Caching mechanism to avoid duplicate queries
    """
    
    def __init__(
        self,
        llm_provider: LLMProvider | None = None,
        search_api_key: str | None = None,
        search_api_url: str | None = None,
        enable_cache: bool = True,
    ):
        self.llm_provider = llm_provider
        self.search_api_key = search_api_key
        self.search_api_url = search_api_url or "https://api.example.com/search"
        self.enable_cache = enable_cache
        self._cache: dict[str, EvidencePack] = {}
    
    def _generate_cache_key(self, spec: ClarifiedSpec) -> str:
        """Generate a cache key based on specification content."""
        key_content = f"{spec.topic}|{spec.audience}|{spec.use_case}"
        return hashlib.md5(key_content.encode()).hexdigest()
    
    def _get_from_cache(self, spec: ClarifiedSpec) -> EvidencePack | None:
        """Retrieve evidence pack from cache if available."""
        if not self.enable_cache:
            return None
        
        cache_key = self._generate_cache_key(spec)
        if cache_key in self._cache:
            logger.info(f"Cache hit for query: {spec.topic}")
            return self._cache[cache_key]
        
        return None
    
    def _save_to_cache(self, spec: ClarifiedSpec, evidence_pack: EvidencePack) -> None:
        """Save evidence pack to cache."""
        if not self.enable_cache:
            return
        
        cache_key = self._generate_cache_key(spec)
        self._cache[cache_key] = evidence_pack
        logger.info(f"Cached evidence pack for: {spec.topic}")
    
    async def _perform_web_search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        """
        Perform web search using external API.
        
        Args:
            query: Search query string
            num_results: Number of results to fetch
            
        Returns:
            List of SearchResult objects
        """
        if not self.search_api_key:
            logger.warning("Search API key not configured. Returning empty search results.")
            return []
        
        try:
            import httpx
            
            headers = {"Authorization": f"Bearer {self.search_api_key}"}
            params = {"q": query, "num": num_results}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.search_api_url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("results", []):
                    results.append(
                        SearchResult(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            snippet=item.get("snippet", ""),
                            source=item.get("source", "web_search"),
                        )
                    )
                
                logger.info(f"Web search returned {len(results)} results for query: {query}")
                return results
                
        except Exception as e:
            logger.error(f"Web search failed for query '{query}': {e}")
            return []
    
    def _extract_facts_from_search_results(
        self, results: list[SearchResult], query: str
    ) -> tuple[list[EvidenceFact], list[EvidenceSuggestion]]:
        """
        Extract facts and suggestions from search results.
        
        Args:
            results: List of SearchResult objects
            query: Original search query
            
        Returns:
            Tuple of (facts, suggestions)
        """
        facts = []
        suggestions = []
        
        for idx, result in enumerate(results, start=1):
            # Create source from search result
            source = EvidenceSource(
                source_type="web_search",
                title=result.title,
                uri=result.url,
                reliability=0.75,  # Web sources have moderate reliability
            )
            
            # Add fact from snippet
            if result.snippet:
                facts.append(
                    EvidenceFact(
                        fact_id=f"fact-web-{idx}",
                        claim=result.snippet,
                        source=source,
                    )
                )
            
            # Generate suggestion based on result title
            suggestions.append(
                EvidenceSuggestion(
                    suggestion_id=f"suggestion-web-{idx}",
                    text=f"Consider including information from: {result.title}",
                    rationale=f"Found via web search for: {query}",
                    confidence=0.7,
                )
            )
        
        return facts, suggestions
    
    def _extract_facts_from_documents(
        self, documents: list[SourceDocument]
    ) -> tuple[list[EvidenceFact], list[EvidenceSuggestion]]:
        """
        Extract facts and suggestions from uploaded documents.
        
        Args:
            documents: List of SourceDocument objects
            
        Returns:
            Tuple of (facts, suggestions)
        """
        facts = []
        suggestions = []
        
        for doc_index, document in enumerate(documents, start=1):
            source = EvidenceSource(
                source_type=document.source_type,
                title=document.title,
                uri=document.uri,
                reliability=0.9 if document.source_type == "user_upload" else 0.75,
            )
            
            for line in [line.strip() for line in document.content.splitlines() if line.strip()]:
                if line.startswith("FACT:"):
                    claim = line.removeprefix("FACT:").strip()
                    facts.append(
                        EvidenceFact(
                            fact_id=f"fact-doc-{doc_index}-{len(facts) + 1}",
                            claim=claim,
                            source=source,
                        )
                    )
                elif line.startswith("SUGGESTION:"):
                    suggestion = line.removeprefix("SUGGESTION:").strip()
                    suggestions.append(
                        EvidenceSuggestion(
                            suggestion_id=f"suggestion-doc-{doc_index}-{len(suggestions) + 1}",
                            text=suggestion,
                            rationale=f"Derived from source {doc_index}: {document.title}",
                        )
                    )
        
        logger.info(f"Extracted {len(facts)} facts and {len(suggestions)} suggestions from {len(documents)} documents")
        return facts, suggestions
    
    def build(
        self,
        spec: ClarifiedSpec,
        documents: list[SourceDocument] | None = None,
        perform_web_search: bool = False,
    ) -> EvidencePack:
        """
        Build comprehensive evidence pack from multiple sources.
        
        Args:
            spec: Clarified specification
            documents: Optional list of source documents
            perform_web_search: Whether to perform web search
            
        Returns:
            EvidencePack with aggregated facts and suggestions
        """
        documents = documents or []
        
        # Check cache first
        cached_result = self._get_from_cache(spec)
        if cached_result and not documents and not perform_web_search:
            return cached_result
        
        all_facts: list[EvidenceFact] = []
        all_suggestions: list[EvidenceSuggestion] = []
        search_queries: list[str] = []
        
        # Extract from uploaded documents
        doc_facts, doc_suggestions = self._extract_facts_from_documents(documents)
        all_facts.extend(doc_facts)
        all_suggestions.extend(doc_suggestions)
        
        # Perform web search if enabled
        if perform_web_search and self.llm_provider:
            # Generate search queries from spec
            search_query = f"{spec.topic} {spec.use_case} {spec.audience}".strip()
            search_queries.append(search_query)
            
            import asyncio
            
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            search_results = loop.run_until_complete(self._perform_web_search(search_query))
            web_facts, web_suggestions = self._extract_facts_from_search_results(search_results, search_query)
            all_facts.extend(web_facts)
            all_suggestions.extend(web_suggestions)
        
        # Fallback: generate suggestions from spec requirements
        if not documents and not perform_web_search:
            for item in spec.must_include:
                all_suggestions.append(
                    EvidenceSuggestion(
                        suggestion_id=f"suggestion-{len(all_suggestions) + 1}",
                        text=f"Include a slide about {item}.",
                        rationale="Derived from explicit user requirement.",
                    )
                )
        
        # Build constraints
        constraints = [f"Avoid: {item}" for item in spec.must_avoid] + [
            f"Must include: {item}" for item in spec.must_include
        ]
        
        evidence_pack = EvidencePack(
            facts=all_facts,
            suggestions=all_suggestions,
            constraints=constraints,
            search_queries=search_queries,
        )
        
        # Save to cache
        self._save_to_cache(spec, evidence_pack)
        
        return evidence_pack
