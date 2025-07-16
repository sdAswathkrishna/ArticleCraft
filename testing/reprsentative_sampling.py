import pandas as pd
import numpy as np
import pickle
import os
import re
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import MiniBatchKMeans
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import gc
from tqdm import tqdm

class RepresentativeSampler:
    def __init__(self, input_file, output_dir, chunk_size=10000, batch_size=32):
        """
        Initialize the representative sampler.
        
        Args:
            input_file: Path to input data (CSV or pickle)
            output_dir: Directory to save outputs
            chunk_size: Number of samples to process at once
            batch_size: Batch size for the sentence transformer
        """
        self.input_file = input_file
        self.output_dir = output_dir
        self.chunk_size = chunk_size
        self.batch_size = batch_size
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
    def compute_embeddings(self, texts):
        """Compute embeddings for texts in batches"""
        all_embeddings = []
        
        # Process in batches to avoid memory issues
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i+self.batch_size]
            batch_embeddings = self.model.encode(batch)
            all_embeddings.append(batch_embeddings)
            
        return np.vstack(all_embeddings)
    
    def score_samples(self, texts, clean_texts, embeddings, cluster_labels):
        """Score each sample based on length, keyword richness, and uniqueness"""
        scores = []
        
        # Calculate TF-IDF to measure keyword richness
        tfidf = TfidfVectorizer()
        tfidf_matrix = tfidf.fit_transform(clean_texts)
        
        # Get centroids of clusters for uniqueness calculation
        centroids = []
        for label in np.unique(cluster_labels):
            cluster_indices = np.where(cluster_labels == label)[0]
            centroid = np.mean(embeddings[cluster_indices], axis=0)
            centroids.append((label, centroid))
        
        for i, (text, clean_text) in enumerate(zip(texts, clean_texts)):
            # Skip empty texts
            if pd.isna(text) or text == "":
                scores.append(0)
                continue
                
            # Length score (normalized)
            length_score = min(len(text.split()) / 100, 1.0)
            
            # Keyword richness (average TF-IDF)
            richness_score = np.mean(tfidf_matrix[i].toarray())
            
            # Uniqueness (distance from centroid)
            cluster_label = cluster_labels[i]
            centroid_vector = next(c[1] for c in centroids if c[0] == cluster_label)
            uniqueness_score = 1 - cosine_similarity([embeddings[i]], [centroid_vector])[0][0]
            
            # Combined score (equal weighting)
            combined_score = (length_score + richness_score + uniqueness_score) / 3
            scores.append(combined_score)
        
        return np.array(scores)
    
    def select_representatives(self, df_chunk, cluster_labels, scores, n_per_cluster=5):
        """Select top-N samples from each cluster based on scores"""
        selected_indices = []
        
        for label in np.unique(cluster_labels):
            cluster_indices = np.where(cluster_labels == label)[0]
            cluster_scores = scores[cluster_indices]
            
            # Get top N indices within this cluster
            if len(cluster_indices) <= n_per_cluster:
                top_n_indices = cluster_indices
            else:
                top_n = np.argsort(cluster_scores)[-n_per_cluster:]
                top_n_indices = cluster_indices[top_n]
                
            selected_indices.extend(top_n_indices)
        
        return df_chunk.iloc[selected_indices]
    
    def process_chunk(self, df_chunk, n_clusters=10, n_per_cluster=5):
        """Process a single chunk of data using pre-processed text fields"""
        # Filter out empty texts
        non_empty_indices = df_chunk['clean_text'].str.strip().astype(bool)
        df_filtered = df_chunk[non_empty_indices].reset_index(drop=True)
        
        if len(df_filtered) == 0:
            return pd.DataFrame()
            
        # Step 1: Use pre-processed text for embeddings
        # We'll use lemmatized text for better semantic understanding
        print("Computing embeddings...")
        embedding_texts = df_filtered['lemmatized'].tolist()
        
        # Convert list-like strings back to actual lists if needed
        if isinstance(embedding_texts[0], str) and embedding_texts[0].startswith('['):
            # This assumes the lemmatized field is stored as a string representation of a list
            embedding_texts = [' '.join(eval(text)) if isinstance(text, str) else ' '.join(text) for text in embedding_texts]
        
        embeddings = self.compute_embeddings(embedding_texts)
        
        # Step 2: Cluster
        print(f"Clustering into {n_clusters} clusters...")
        n_clusters = min(n_clusters, len(df_filtered))  # Ensure we don't have more clusters than samples
        kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, batch_size=self.batch_size)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # Step 3: Score samples
        print("Scoring samples...")
        scores = self.score_samples(
            df_filtered['text'].tolist(), 
            df_filtered['clean_text'].tolist(), 
            embeddings, 
            cluster_labels
        )
        
        # Step 4: Select representatives
        print(f"Selecting top {n_per_cluster} samples per cluster...")
        selected_samples = self.select_representatives(df_filtered, cluster_labels, scores, n_per_cluster)
        
        return selected_samples
    
    def process_in_chunks(self, n_clusters=10, n_per_cluster=5):
        """Process the entire dataset in chunks"""
        # Determine file type and reader
        if self.input_file.endswith('.csv'):
            reader = pd.read_csv
        elif self.input_file.endswith('.pkl') or self.input_file.endswith('.pickle'):
            reader = pd.read_pickle
        else:
            raise ValueError("Input file must be CSV or pickle")
        
        # Initialize an empty list to store selected samples
        all_selected_samples = []
        
        # Process in chunks
        for chunk_idx, df_chunk in enumerate(tqdm(reader(self.input_file, chunksize=self.chunk_size))):
            print(f"\nProcessing chunk {chunk_idx+1}")
            
            # Ensure required columns exist
            required_columns = ['text', 'clean_text', 'lemmatized']
            missing_columns = [col for col in required_columns if col not in df_chunk.columns]
            if missing_columns:
                raise ValueError(f"Required columns missing: {missing_columns}")
            
            # Process chunk
            selected_samples = self.process_chunk(df_chunk, n_clusters, n_per_cluster)
            
            # Add to overall results
            if not selected_samples.empty:
                all_selected_samples.append(selected_samples)
            
            # Free memory
            del df_chunk, selected_samples
            gc.collect()
        
        # Combine all selected samples
        if all_selected_samples:
            final_df = pd.concat(all_selected_samples, ignore_index=True)
            
            # Save results
            final_df.to_csv(os.path.join(self.output_dir, 'representative_samples.csv'), index=False)
            final_df.to_pickle(os.path.join(self.output_dir, 'representative_samples.pkl'))
            
            print(f"Selected {len(final_df)} representative samples out of the entire dataset")
            return final_df
        else:
            print("No samples were selected.")
            return pd.DataFrame()

# Example usage
if __name__ == "__main__":
    # Configuration
    input_file = "final_nlp_data.csv"  # or preprocessed_data.pkl
    output_dir = "representative_samples"
    
    # Initialize the sampler
    sampler = RepresentativeSampler(
        input_file=input_file,
        output_dir=output_dir,
        chunk_size=10000,  # Adjust based on available memory
        batch_size=168
    )
    
    # Process the data
    representative_df = sampler.process_in_chunks(
        n_clusters=20,       # Number of clusters per chunk
        n_per_cluster=5      # Number of samples to select per cluster
    )