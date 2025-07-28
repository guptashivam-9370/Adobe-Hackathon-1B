# app/relevance_analyzer.py
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class RelevanceAnalyzer:
    def __init__(self, model_path="./sbert_model"):
        """Initializes the analyzer by loading the sentence-transformer model."""
        # Load the model from the path where we saved it
        self.model = SentenceTransformer(model_path)

    def analyze(self, query, sections):
        """
        Ranks sections based on their semantic similarity to a query.
        
        Args:
            query (str): The user's query (Persona + Job-to-be-Done).
            sections (list of dicts): A list of sections from the documents.
                                      Each dict needs a 'content' key.

        Returns:
            A list of sections sorted by relevance, with a 'relevance_score' added.
        """
        if not sections:
            return []

        # Generate embeddings for the query and all section contents
        query_embedding = self.model.encode([query])
        section_contents = [s['content'] for s in sections]
        section_embeddings = self.model.encode(section_contents)

        # Calculate cosine similarity
        similarities = cosine_similarity(query_embedding, section_embeddings)[0]

        # Add the score to each section and sort
        for section, score in zip(sections, similarities):
            section['relevance_score'] = score
        
        sorted_sections = sorted(sections, key=lambda s: s['relevance_score'], reverse=True)
        
        return sorted_sections