import os
import pandas as pd
import time
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

class ArticleGenerator:
    def __init__(self, groq_api_key=None, model_name="Llama3-8b-8192"):
        """
        Initialize the article generator with Groq LLM.
        
        Parameters:
        -----------
        groq_api_key : str
            Groq API key (will use environment variable if None)
        model_name : str
            Name of the Groq model to use
        """
        # Load environment variables if not already done
        load_dotenv()
        
        # Set API key (from parameter or environment)
        self.groq_api_key = groq_api_key or os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            raise ValueError("Groq API key not provided and not found in environment variables")
        
        # Initialize LLM
        self.llm = ChatGroq(
            groq_api_key=self.groq_api_key,
            model_name=model_name
        )
        
        # Set up article generation prompt
        self.article_prompt = ChatPromptTemplate.from_template("""
        You are an expert article writer. Generate a well-structured article based on the provided title.
        Use the following similar articles as reference to match the style, tone, and format, but create original content.

        REFERENCE ARTICLES:
        {context}

        TITLE TO GENERATE ARTICLE FOR:
        {input}

        Write a comprehensive, engaging, and well-structured article for the given title. 
        The article should be factually accurate, well-researched, and follow a logical flow.
        Include an introduction, several body paragraphs with relevant subheadings, and a conclusion.
        Aim for approximately 800-1000 words.
        Do not mention that you're using reference articles - write as if you are the original author.
        """)
        
        # Storage for vector database
        self.vector_store = None
    
    def load_article_data(self, file_path):
        """
        Load article data from CSV file.
        
        Parameters:
        -----------
        file_path : str
            Path to the CSV file containing article data
            
        Returns:
        --------
        pandas.DataFrame or None
            Loaded article data or None if loading failed
        """
        try:
            df = pd.read_csv(file_path)
            print(f"Loaded {len(df)} articles from dataset")
            
            # Validate columns
            if 'title' not in df.columns or 'text' not in df.columns:
                raise ValueError("CSV must contain 'title' and 'text' columns")
                
            return df
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return None
    
    def create_vector_embeddings(self, df, sample_size=1000):
        """
        Create vector embeddings from article data.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame containing article data
        sample_size : int
            Maximum number of articles to use for embeddings
            
        Returns:
        --------
        FAISS vector store
        """
        # Sample data if needed
        if len(df) > sample_size:
            df_sample = df.sample(sample_size, random_state=42)
            print(f"Using {sample_size} articles for vector database")
        else:
            df_sample = df
            print(f"Using all {len(df)} articles for vector database")
        
        # Convert dataframe rows to Document objects
        # This is the fix: using proper Document objects instead of dictionaries
        documents = []
        for _, row in df_sample.iterrows():
            # Combine title and text to create a full document
            content = f"Title: {row['title']}\n\n{row['text']}"
            # Create a proper Document object
            doc = Document(
                page_content=content,
                metadata={"title": row['title']}
            )
            documents.append(doc)
        
        # Initialize the text splitter
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        
        # Process documents into chunks
        splits = text_splitter.split_documents(documents)
        
        # Create vector embeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vector_store = FAISS.from_documents(splits, embeddings)
        
        return vector_store
    
    def setup_vector_database(self, file_path, sample_size=1000):
        """
        Set up the vector database from the article data file.
        
        Parameters:
        -----------
        file_path : str
            Path to the CSV file containing article data
        sample_size : int
            Maximum number of articles to use for embeddings
        """
        # Load data
        df = self.load_article_data(file_path)
        if df is None:
            raise ValueError("Failed to load article data")
        
        # Create vector embeddings
        print("Creating vector embeddings from articles...")
        self.vector_store = self.create_vector_embeddings(df, sample_size)
        print("Vector database created successfully!")
    
    def generate_article(self, title, num_similar_articles=3):
        """
        Generate an article based on the provided title.
        
        Parameters:
        -----------
        title : str
            Title of the article to generate
        num_similar_articles : int
            Number of similar articles to use as reference
            
        Returns:
        --------
        dict
            Generated article and metadata
        """
        if self.vector_store is None:
            raise ValueError("Vector database not initialized. Call setup_vector_database() first.")
        
        start_time = time.process_time()
        
        # Create retrieval chain
        retriever = self.vector_store.as_retriever(search_kwargs={"k": num_similar_articles})
        document_chain = create_stuff_documents_chain(self.llm, self.article_prompt)
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        
        # Generate the article
        response = retrieval_chain.invoke({"input": title})
        generation_time = time.process_time() - start_time
        
        # Add generation metadata
        result = {
            "title": title,
            "article": response["answer"],
            "reference_articles": response["context"],
            "generation_time_seconds": generation_time
        }
        
        print(f"Article generated in {generation_time:.2f} seconds")
        return result
    
    def save_article_to_file(self, result, output_path=None):
        """
        Save the generated article to a file.
        
        Parameters:
        -----------
        result : dict
            Result from generate_article()
        output_path : str, optional
            Path to save the article (if None, uses title)
        """
        if output_path is None:
            output_path = f"{result['title'].replace(' ', '_')}.md"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# {result['title']}\n\n")
            f.write(result['article'])
        
        print(f"Article saved to {output_path}")


# Example usage
if __name__ == "__main__":
    # Initialize the article generator
    generator = ArticleGenerator()
    
    # Set up the vector database
    generator.setup_vector_database(
        file_path="final_nlp_data.csv",
        sample_size=1000
    )
    
    # Generate an article
    article_result = generator.generate_article(
        title="The Impact of Artificial Intelligence on Modern Healthcare",
        num_similar_articles=3
    )
    
    # Print the generated article
    print("\n" + "="*50)
    print(f"Generated Article: {article_result['title']}")
    print("="*50)
    print(article_result['article'][:1000] + "..." if len(article_result['article']) > 1000 else article_result['article'])
    
    # Save the article to a file
    generator.save_article_to_file(article_result)