#!/usr/bin/env python3
"""
Test FAISS vector store functionality.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
import tempfile
import shutil
import consts
from config import Config
from vector_store_faiss import FAISSVectorStore

class TestVectorStore(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        self.config = Config(consts.CONFIG_PATH)
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test vector store initialization."""
        store = FAISSVectorStore(self.config, persist_directory=self.temp_dir)
        self.assertIsNotNone(store.embedding_function)
        self.assertIsNotNone(store.index)
    
    def test_add_and_search(self):
        """Test adding documents and searching."""
        store = FAISSVectorStore(self.config, persist_directory=self.temp_dir)
        
        # Add test documents
        texts = [
            "Gamma is the rate of change of delta with respect to the underlying price.",
            "0DTE options are zero days to expiration options.",
            "Volatility smile shows implied volatility across different strikes."
        ]
        metadatas = [
            {"source": "test1", "title": "Gamma Definition"},
            {"source": "test2", "title": "0DTE Options"}, 
            {"source": "test3", "title": "Volatility Smile"}
        ]
        
        store.add_texts(texts, metadatas=metadatas)
        # FAISS doesn't return IDs, so just verify we can search
        
        # Test search
        results = store.similarity_search("What is gamma?", k=2)
        self.assertEqual(len(results), 2)
        self.assertIn("gamma", results[0][0].lower())
    
    def test_persistence(self):
        """Test saving and loading from disk."""
        store1 = FAISSVectorStore(self.config, persist_directory=self.temp_dir)
        
        # Add documents
        texts = ["Test document about options trading"]
        metadatas = [{"source": "test_persist", "title": "Test"}]
        store1.add_texts(texts, metadatas=metadatas)
        
        # Create new store from saved data
        store2 = FAISSVectorStore(self.config, persist_directory=self.temp_dir)
        
        # Should find the document
        results = store2.similarity_search("options trading", k=1)
        self.assertEqual(len(results), 1)
        self.assertIn("options trading", results[0][0])
    
    def test_similarity_search_with_score(self):
        """Test similarity search with scores."""
        store = FAISSVectorStore(self.config, persist_directory=self.temp_dir)
        
        # Add test documents
        texts = [
            "Gamma squeeze happens when market makers hedge their positions.",
            "Delta hedging is a strategy to maintain delta neutrality.",
            "Theta decay accelerates as options approach expiration."
        ]
        metadatas = [
            {"source": "gamma_doc", "title": "Gamma Squeeze"},
            {"source": "delta_doc", "title": "Delta Hedging"},
            {"source": "theta_doc", "title": "Theta Decay"}
        ]
        
        store.add_texts(texts, metadatas=metadatas)
        
        # Search with scores
        results = store.similarity_search_with_score("gamma squeeze mechanics", k=2)
        self.assertEqual(len(results), 2)
        
        # First result should be about gamma squeeze
        self.assertIn("gamma squeeze", results[0][0].page_content.lower())
        self.assertIsInstance(results[0][1], float)
        
        # Scores should be ordered (lower is better for L2 distance)
        self.assertLessEqual(results[0][1], results[1][1])
    
    def test_empty_search(self):
        """Test searching empty vector store."""
        store = FAISSVectorStore(self.config, persist_directory=self.temp_dir)
        results = store.similarity_search("test query", k=5)
        self.assertEqual(len(results), 0)
    
    def test_metadata_filtering(self):
        """Test that metadata is properly stored and retrieved."""
        store = FAISSVectorStore(self.config, persist_directory=self.temp_dir)
        
        # Add documents with metadata
        texts = ["SpotGamma analysis of market dynamics"]
        metadatas = [{
            "source": "abc123",
            "title": "Market Analysis",
            "url": "https://youtube.com/watch?v=abc123"
        }]
        
        store.add_texts(texts, metadatas=metadatas)
        
        # Search and verify metadata
        results = store.similarity_search("SpotGamma", k=1)
        self.assertEqual(len(results), 1)
        
        doc, metadata = results[0]
        self.assertEqual(metadata["source"], "abc123")
        self.assertEqual(metadata["title"], "Market Analysis")
        self.assertIn("youtube.com", metadata["url"])

if __name__ == '__main__':
    unittest.main()