import pandas as pd
import joblib


# Load models
tfidf = joblib.load('models/tfidf_vectorizer.pkl')
tfidf_matrix = joblib.load('models/tfidf_matrix.pkl')
nn = joblib.load('models/nearest_neighbors.pkl')
df = pd.read_pickle('final_nlp_data.pkl')  # Load corresponding article metadata

def recommend_articles(query, top_k=5):
    # Transform query using TF-IDF
    query_vec = tfidf.transform([query])
    
    # Find nearest neighbors
    distances, indices = nn.kneighbors(query_vec, n_neighbors=top_k)
    
    # Fetch and return results
    results = df.iloc[indices[0]].copy()
    results["similarity"] = 1 - distances[0]  # Cosine similarity = 1 - distance
    return results[["clean_title", "similarity", "clean_text"]]


if __name__ == "__main__":
    query = "Recent advancements in AI for healthcare"
    recommendations = recommend_articles(query, top_k=5)
    print(recommendations)

