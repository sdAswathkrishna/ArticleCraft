import os
import joblib
import pandas as pd
from typing import Optional, Dict, Any
from generate_module import ArticleGenerator
from nextword_module import load_model_and_tokenizer, generate_next_words
from recommendation_module import recommend_articles

class AIServices:
    """Service class to manage all AI models"""
    
    def __init__(self):
        self.article_generator: Optional[ArticleGenerator] = None
        self.nextword_model = None
        self.nextword_tokenizer = None
        self.recommendation_models: Optional[Dict[str, Any]] = None
        
    async def load_all_models(self):
        """Load all AI models at startup"""
        print("Loading AI models...")
        
        # Load Article Generator
        try:
            self.article_generator = ArticleGenerator()
            if os.path.exists("vector_db"):
                self.article_generator.load_vector_database()
            else:
                print("Vector database not found, creating new one...")
                self.article_generator.setup_vector_database("final_nlp_data.csv", sample_size=1000)
            print("✓ Article Generator loaded")
        except Exception as e:
            print(f"❌ Failed to load Article Generator: {e}")
            self.article_generator = None
        
        # Load Next Word Model
        try:
            self.nextword_model, self.nextword_tokenizer = load_model_and_tokenizer()
            print("✓ Next Word Model loaded")
        except Exception as e:
            print(f"❌ Failed to load Next Word Model: {e}")
            self.nextword_model = None
            self.nextword_tokenizer = None
        
        # Load Recommendation Models
        try:
            self.recommendation_models = {
                'tfidf': joblib.load('models/tfidf_vectorizer.pkl'),
                'tfidf_matrix': joblib.load('models/tfidf_matrix.pkl'),
                'nn': joblib.load('models/nearest_neighbors.pkl'),
                'df': pd.read_pickle('models/cleaned_articles.pkl')
            }
            print("✓ Recommendation Models loaded")
        except Exception as e:
            print(f"❌ Failed to load Recommendation Models: {e}")
            self.recommendation_models = None
        
        print("AI Services initialization complete!")
    
    def generate_article(self, title: str, num_similar_articles: int = 3) -> Dict[str, Any]:
        """Generate article using AI"""
        if self.article_generator is None:
            raise ValueError("Article generator not available")
        
        return self.article_generator.generate_article(title, num_similar_articles)
    
    def generate_next_words(self, seed_text: str, next_words: int = 5, temperature: float = 1.0) -> str:
        """Generate next words using LSTM model"""
        if self.nextword_model is None or self.nextword_tokenizer is None:
            raise ValueError("Next word model not available")
        
        return generate_next_words(
            seed_text=seed_text,
            next_words=next_words,
            model=self.nextword_model,
            tokenizer=self.nextword_tokenizer,
            max_seq_len=30,
            temperature=temperature
        )
    
    def get_recommendations(self, query: str, top_k: int = 5) -> pd.DataFrame:
        """Get article recommendations"""
        if self.recommendation_models is None:
            raise ValueError("Recommendation models not available")
        
        return recommend_articles(query, top_k=top_k)
    
    def get_similar_articles(self, article_title: str, top_k: int = 10) -> list:
        """Get similar articles based on title"""
        if self.recommendation_models is None:
            raise ValueError("Recommendation models not available")
        
        df = self.recommendation_models['df']
        tfidf_matrix = self.recommendation_models['tfidf_matrix']
        nn = self.recommendation_models['nn']
        
        if article_title not in df['clean_title'].values:
            return []
        
        idx = df[df['clean_title'] == article_title].index[0]
        query_vector = tfidf_matrix[idx]
        
        distances, indices = nn.kneighbors(query_vector, n_neighbors=top_k + 1)  # +1 to exclude self
        similar_indices = indices.flatten()[1:]  # exclude self
        
        recommendations = df[['clean_title', 'clean_text']].iloc[similar_indices].to_dict(orient='records')
        return recommendations[:top_k]
    
    def is_available(self) -> Dict[str, bool]:
        """Check which services are available"""
        return {
            "article_generator": self.article_generator is not None,
            "nextword_model": self.nextword_model is not None and self.nextword_tokenizer is not None,
            "recommendation_models": self.recommendation_models is not None
        }

# Global instance
ai_services = AIServices()