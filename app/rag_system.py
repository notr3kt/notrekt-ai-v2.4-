#!/usr/bin/env python3
"""
NOTREKT.AI v2.0 - Zero-Guessing RAG System
Retrieval-Augmented Generation with trusted knowledge corpus and source verification.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import pickle


# Optional dependencies for RAG functionality
DEPENDENCIES_AVAILABLE = True
np = None
SentenceTransformer = None
faiss = None

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    import faiss
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    print(f"Warning: RAG dependencies not installed: {e}")
    print("Install with: pip install sentence-transformers faiss-cpu numpy")
    # Create dummy objects to prevent import errors
    class DummyModel:
        def __init__(self, *args, **kwargs):
            pass
        def encode(self, x):
            raise ImportError("sentence-transformers not installed")
        def get_sentence_embedding_dimension(self):
            return 384
    SentenceTransformer = DummyModel
    class DummyFaiss:
        @staticmethod
        def read_index(*args, **kwargs):
            raise ImportError("faiss not installed")
        @staticmethod
        def write_index(*args, **kwargs):
            raise ImportError("faiss not installed")
        class IndexFlatIP:
            def __init__(self, *args, **kwargs):
                pass
            def add(self, *args, **kwargs):
                pass
            def search(self, *args, **kwargs):
                return [[0.0]], [[-1]]
            @property
            def ntotal(self):
                return 0
    faiss = DummyFaiss

from .config_manager import Config, logger

# --- RAG Answer Synthesis and [GAP] Handling ---
def synthesize_answer(query: str, search_results: list) -> dict:
    """
    Synthesize a coherent answer from search results, with source citations.
    If no verifiable answer, return a [GAP] marker.
    """
    if not search_results:
        return {
            "answer": "[GAP: No verifiable answer found for query]",
            "sources": [],
            "status": "gap"
        }
    # Example: concatenate top results with citations
    answer_parts = []
    sources = []
    for res in search_results:
        snippet = res.get("snippet") or res.get("text") or str(res)
        source = res.get("source") or res.get("doc_id") or "unknown"
        answer_parts.append(f"{snippet} (source: {source})")
        sources.append(source)
    answer = "\n".join(answer_parts)
    return {
        "answer": answer,
        "sources": sources,
        "status": "ok"
    }

@dataclass
class Document:
    """Represents a document in the trusted knowledge corpus."""
    id: str
    title: str
    content: str
    source_path: str
    metadata: Dict[str, Any]
    hash: str
    indexed_at: str

@dataclass
class SearchResult:
    """Represents a search result from the vector store."""
    document: Document
    score: float
    excerpt: str

class VectorStore:
    """
    Vector store for document embeddings using FAISS and sentence-transformers.
    Provides semantic search capabilities over trusted knowledge corpus.
    """
    
    def __init__(self, corpus_path: Optional[str] = None, vector_db_path: Optional[str] = None):
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("RAG system requires numpy, sentence-transformers, and faiss-cpu. Install with: pip install sentence-transformers faiss-cpu numpy")
            
        self.corpus_path = Path(corpus_path or Config.CORPUS_PATH)
        self.vector_db_path = Path(vector_db_path or Config.VECTOR_DB_PATH)
        
        # Ensure directories exist
        self.corpus_path.mkdir(parents=True, exist_ok=True)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize sentence transformer model
        try:
            if SentenceTransformer is None:
                raise ImportError("sentence-transformers not installed")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            if not hasattr(self.model, 'get_sentence_embedding_dimension'):
                raise ImportError("sentence-transformers model missing get_sentence_embedding_dimension")
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")
            raise
        
        # Initialize FAISS index
        self.index = None
        self.documents: List[Document] = []
        
        # Load existing index if available
        self._load_index()
        
        logger.info(f"VectorStore initialized with {len(self.documents)} documents")
    
    def _load_index(self):
        """Load existing FAISS index and documents from disk."""
        index_path = self.vector_db_path / "faiss_index.bin"
        docs_path = self.vector_db_path / "documents.pkl"
        
        if index_path.exists() and docs_path.exists():
            try:
                # Load FAISS index
                if faiss is not None and hasattr(faiss, 'read_index'):
                    self.index = faiss.read_index(str(index_path))
                else:
                    self.index = None
                # Load documents
                with open(docs_path, 'rb') as f:
                    self.documents = pickle.load(f)
                logger.info(f"Loaded existing index with {len(self.documents)} documents")
                # Verify index and documents are in sync
                if self.index is not None and hasattr(self.index, 'ntotal') and self.index.ntotal != len(self.documents):
                    logger.warning("Index and documents out of sync, rebuilding...")
                    self._rebuild_index()
            except Exception as e:
                logger.error(f"Failed to load existing index: {e}")
                self._rebuild_index()
        else:
            logger.info("No existing index found, will build new one")
            self._rebuild_index()
    
    def _save_index(self):
        """Save FAISS index and documents to disk."""
        try:
            # Save FAISS index
            index_path = self.vector_db_path / "faiss_index.bin"
            if faiss is not None and hasattr(faiss, 'write_index') and self.index is not None:
                faiss.write_index(self.index, str(index_path))
            # Save documents
            docs_path = self.vector_db_path / "documents.pkl"
            with open(docs_path, 'wb') as f:
                pickle.dump(self.documents, f)
            logger.info(f"Saved index with {len(self.documents)} documents")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    def _rebuild_index(self):
        """Rebuild the entire vector index from corpus files."""
        logger.info("Rebuilding vector index from corpus...")
        
        # Clear existing data
        self.documents = []
        
        # Initialize new FAISS index
        if faiss is not None and hasattr(faiss, 'IndexFlatIP'):
            self.index = faiss.IndexFlatIP(self.embedding_dim)
        else:
            self.index = None
        # Index all documents in corpus
        self.index_corpus()
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _extract_text_from_file(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text content and metadata from various file types.
        Currently supports: .txt, .md, .json
        """
        try:
            suffix = file_path.suffix.lower()
            
            if suffix in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                metadata = {
                    "file_type": suffix,
                    "size_bytes": file_path.stat().st_size,
                    "last_modified": file_path.stat().st_mtime
                }
                return content, metadata
            
            elif suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Convert JSON to readable text
                content = json.dumps(data, indent=2)
                metadata = {
                    "file_type": "json",
                    "size_bytes": file_path.stat().st_size,
                    "last_modified": file_path.stat().st_mtime,
                    "json_keys": list(data.keys()) if isinstance(data, dict) else []
                }
                return content, metadata
            
            else:
                logger.warning(f"Unsupported file type: {suffix}")
                return "", {"file_type": suffix, "error": "unsupported_format"}
                
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            return "", {"error": str(e)}
    
    def _chunk_text(self, text, chunk_size=500):
        import re
        sentences = re.split(r'(?<=[.!?]) +', text)
        chunks, current = [], ""
        for s in sentences:
            if len(current) + len(s) < chunk_size:
                current += s + " "
            else:
                chunks.append(current.strip())
                current = s + " "
        if current:
            chunks.append(current.strip())
        return chunks

    def index_document(self, file_path: Path) -> Optional[str]:
        """
        Index a single document from file path.
        Returns document ID if successful, None if failed.
        """
        try:
            # Extract content and metadata
            content, file_metadata = self._extract_text_from_file(file_path)
            if not content.strip():
                logger.warning(f"No content extracted from {file_path}")
                return None
            # Calculate file hash for change detection
            file_hash = self._calculate_file_hash(file_path)
            # Check if document already exists with same hash
            for doc in self.documents:
                if doc.source_path == str(file_path) and doc.hash == file_hash:
                    logger.debug(f"Document unchanged, skipping: {file_path}")
                    return doc.id
            # Chunk document
            chunks = self._chunk_text(content)
            doc_id = hashlib.sha256(str(file_path).encode()).hexdigest()[:16]
            for idx, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_{idx}"
                document = Document(
                    id=chunk_id,
                    title=f"{file_path.stem}_chunk{idx}",
                    content=chunk,
                    source_path=str(file_path),
                    metadata=file_metadata,
                    hash=file_hash,
                    indexed_at=datetime.utcnow().isoformat() + "Z"
                )
                # Generate embedding
                embedding = None
                if self.model is not None and hasattr(self.model, 'encode'):
                    try:
                        embedding = self.model.encode([chunk])
                    except Exception as e:
                        logger.error(f"Embedding generation failed: {e}")
                        embedding = None
                # Normalize for cosine similarity and add to index
                if embedding is not None and np is not None and hasattr(np, 'linalg'):
                    try:
                        embedding = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)
                        if self.index is not None and hasattr(self.index, 'add'):
                            real_faiss = False
                            try:
                                from faiss import IndexFlatIP  # type: ignore
                                real_faiss = isinstance(self.index, IndexFlatIP)
                            except ImportError:
                                real_faiss = False
                            if real_faiss:
                                try:
                                    self.index.add(embedding.astype('float32'))  # type: ignore[attr-defined]
                                except Exception as e:
                                    logger.error(f"Index add failed: {e}")
                    except Exception as e:
                        logger.error(f"Embedding normalization or index add failed: {e}")
                self.documents.append(document)
            logger.info(f"Indexed document: {file_path} (ID: {doc_id}) with {len(chunks)} chunks")
            return doc_id
        except Exception as e:
            logger.error(f"Failed to index document {file_path}: {e}")
            return None
    
    def index_corpus(self) -> int:
        """
        Index all documents in the corpus directory.
        Returns number of documents successfully indexed.
        """
        logger.info(f"Indexing corpus from: {self.corpus_path}")
        
        if not self.corpus_path.exists():
            logger.warning(f"Corpus path does not exist: {self.corpus_path}")
            return 0
        
        indexed_count = 0
        supported_extensions = {'.txt', '.md', '.json'}
        
        for file_path in self.corpus_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                if self.index_document(file_path):
                    indexed_count += 1
        
        # Save the updated index
        if indexed_count > 0:
            self._save_index()
        
        logger.info(f"Indexing complete: {indexed_count} documents indexed")
        return indexed_count
    
    def search(self, query: str, k: int = 5, min_score: float = 0.3) -> List[SearchResult]:
        """
        Search for documents similar to the query.
        
        Args:
            query: Search query string
            k: Number of results to return
            min_score: Minimum similarity score threshold
        
        Returns:
            List of SearchResult objects
        """
        if not self.documents or self.index is None or not hasattr(self.index, 'ntotal') or self.index.ntotal == 0:
            logger.warning("No documents in index")
            return []
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query]) if self.model is not None and hasattr(self.model, 'encode') else None
            if query_embedding is not None and np is not None:
                query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
                # Search index
                if self.index is not None and hasattr(self.index, 'search'):
                    # Only call search if real faiss (module is 'faiss')
                    # Only call search if real faiss IndexFlatIP (not dummy)
                    real_faiss = False
                    try:
                        from faiss import IndexFlatIP  # type: ignore
                        real_faiss = isinstance(self.index, IndexFlatIP)
                    except ImportError:
                        real_faiss = False
                    if real_faiss:
                        try:
                            scores, indices = self.index.search(query_embedding.astype('float32'), k)  # type: ignore[attr-defined]
                        except Exception as e:
                            logger.error(f"Index search failed: {e}")
                            scores, indices = [[0.0]], [[-1]]
                    else:
                        # Dummy: return fake results, do not call search()
                        scores, indices = [[0.0]], [[-1]]
                    results = []
                    for score, idx in zip(scores[0], indices[0]):
                        if idx == -1 or score < min_score:
                            continue
                        if idx < 0 or idx >= len(self.documents):
                            continue
                        document = self.documents[idx]
                        excerpt = self._extract_excerpt(document.content, query)
                        results.append(SearchResult(
                            document=document,
                            score=float(score),
                            excerpt=excerpt
                        ))
                    logger.info(f"Search query: '{query}' returned {len(results)} results")
                    return results
            return []
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _extract_excerpt(self, content: str, query: str, context_chars: int = 200) -> str:
        """Extract relevant excerpt from document content around query terms."""
        try:
            # Simple keyword-based excerpt extraction
            query_words = query.lower().split()
            content_lower = content.lower()
            
            # Find the first occurrence of any query word
            best_pos = -1
            for word in query_words:
                pos = content_lower.find(word)
                if pos != -1 and (best_pos == -1 or pos < best_pos):
                    best_pos = pos
            
            if best_pos == -1:
                # No direct match, return beginning
                return content[:context_chars * 2] + "..." if len(content) > context_chars * 2 else content
            
            # Extract context around the match
            start = max(0, best_pos - context_chars)
            end = min(len(content), best_pos + context_chars)
            
            excerpt = content[start:end]
            
            # Add ellipsis if truncated
            if start > 0:
                excerpt = "..." + excerpt
            if end < len(content):
                excerpt = excerpt + "..."
            
            return excerpt
            
        except Exception as e:
            logger.error(f"Failed to extract excerpt: {e}")
            return content[:400] + "..." if len(content) > 400 else content

class ResearchAgent:
    def answer(self, query: str, retrieved_sources: list) -> dict:
        """
        Synthesize a response using only retrieved_sources and LLMProvider.
        If answer is not verifiable, return [GAP] and confidence_score.
        """
        from .utils.llm_provider import LLMProvider
        if not retrieved_sources:
            return {
                "answer": "[GAP: Clarification Needed - No verifiable source found for this query]",
                "confidence_score": 0,
                "sources": [],
                "query": query
            }
        # Concatenate sources for LLM prompt
        sources_text = "\n---\n".join(retrieved_sources)
        prompt = (
            f"You are a research assistant. Answer the following query strictly using only the provided sources.\n"
            f"If the answer is not directly verifiable, respond with '[GAP: Clarification Needed - No verifiable source found for this query]'.\n"
            f"Query: {query}\n"
            f"Sources:\n{sources_text}\n"
            f"Answer:"
        )
        llm = LLMProvider("gemini", {})
        answer = llm.generate(prompt)
        # Confidence: crude heuristic—if answer contains a direct quote or matches a source, high; else, low
        confidence = 0
        for src in retrieved_sources:
            if src.strip() and src.strip() in answer:
                confidence = 100
                break
        if confidence == 0 and "[GAP" in answer:
            confidence = 0
        elif confidence == 0:
            confidence = 50
        return {
            "answer": answer,
            "confidence_score": confidence,
            "sources": retrieved_sources,
            "query": query
        }
    """
    Zero-Guessing Research Agent that provides answers grounded only in trusted sources.
    """
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.vector_store = vector_store or VectorStore()
        logger.info("ResearchAgent initialized")
    
    def query(self, question: str, max_sources: int = 3) -> Dict[str, Any]:
        """
        Answer a question using only verified sources from the trusted knowledge corpus.
        
        Args:
            question: The research question
            max_sources: Maximum number of sources to use in the answer
        
        Returns:
            Dictionary with answer, sources, and metadata
        """
        logger.info(f"Research query: {question}")
        
        # Search for relevant documents
        search_results = self.vector_store.search(question, k=max_sources * 2)
        
        if not search_results:
            logger.warning("No relevant sources found for query")
            return {
                "answer": "[GAP: No verifiable source found for this query]",
                "sources": [],
                "confidence": 0.0,
                "query": question,
                "gap_reason": "no_relevant_sources"
            }
        
        # Filter and rank sources
        top_sources = search_results[:max_sources]
        
        # Synthesize answer from sources
        answer_parts = []
        sources_used = []
        
        for i, result in enumerate(top_sources, 1):
            doc = result.document
            
            # Add source information
            source_info = {
                "id": doc.id,
                "title": doc.title,
                "source_path": doc.source_path,
                "relevance_score": result.score,
                "excerpt": result.excerpt
            }
            sources_used.append(source_info)
            
            # Add to answer
            answer_parts.append(f"Source {i} ({doc.title}): {result.excerpt}")
        
        # Combine answer parts
        if answer_parts:
            answer = "Based on trusted sources:\n\n" + "\n\n".join(answer_parts)
            confidence = sum(r.score for r in top_sources) / len(top_sources)
        else:
            answer = "[GAP: Sources found but insufficient confidence in content]"
            confidence = 0.0
        
        result = {
            "answer": answer,
            "sources": sources_used,
            "confidence": round(confidence, 3),
            "query": question,
            "sources_count": len(sources_used)
        }
        
        logger.info(f"Research complete: {len(sources_used)} sources used, confidence: {confidence:.3f}")
        return result
    
    def verify_claim(self, claim: str) -> Dict[str, Any]:
        """
        Verify a specific claim against the trusted knowledge corpus.
        
        Args:
            claim: The claim to verify
        
        Returns:
            Dictionary with verification result
        """
        logger.info(f"Verifying claim: {claim}")
        
        # Search for supporting or contradicting evidence
        search_results = self.vector_store.search(claim, k=10)
        
        if not search_results:
            return {
                "verified": False,
                "confidence": 0.0,
                "reason": "No sources found to verify claim",
                "claim": claim,
                "supporting_sources": [],
                "contradicting_sources": []
            }
        
        # Analyze results for supporting/contradicting evidence
        # This is a simplified implementation - in production, you'd use more sophisticated NLP
        supporting_sources = []
        contradicting_sources = []
        
        for result in search_results:
            if result.score > 0.7:  # High relevance threshold
                supporting_sources.append({
                    "title": result.document.title,
                    "excerpt": result.excerpt,
                    "score": result.score
                })
        
        verification_result = {
            "verified": len(supporting_sources) > 0,
            "confidence": max(r.score for r in search_results) if search_results else 0.0,
            "claim": claim,
            "supporting_sources": supporting_sources,
            "contradicting_sources": contradicting_sources,
            "total_sources_checked": len(search_results)
        }
        
        logger.info(f"Claim verification complete: verified={verification_result['verified']}")
        return verification_result
    
    def get_corpus_stats(self) -> Dict[str, Any]:
        """Get statistics about the trusted knowledge corpus."""
        return {
            "total_documents": len(self.vector_store.documents),
            "corpus_path": str(self.vector_store.corpus_path),
            "index_size": self.vector_store.index.ntotal if self.vector_store.index else 0,
            "embedding_dimension": self.vector_store.embedding_dim
        }
