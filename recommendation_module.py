from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

# Load your final preprocessed DataFrame
import pandas as pd
df = pd.read_pickle('final_nlp_data.pkl')  # Adjust path as needed

tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
tfidf_matrix = tfidf.fit_transform(df['clean_text'])

# Fit Nearest Neighbors
nn = NearestNeighbors(metric='cosine', algorithm='brute')
nn.fit(tfidf_matrix)

# Recommend Function
def recommend_articles_nn(title, df=df, top_n=10):
    if title not in df['title'].values:
        return f"'{title}' not found."

    idx = df[df['title'] == title].index[0]
    query_vector = tfidf_matrix[idx]

    distances, indices = nn.kneighbors(query_vector, n_neighbors=top_n+1)
    
    # Skip self-match
    similar_indices = indices.flatten()[1:]
    
    return df[['title', 'url']].iloc[similar_indices]

recommendations = recommend_articles_nn("Mental Note Vol. 24")
print(recommendations)