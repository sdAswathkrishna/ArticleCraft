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
# from sentence_transformers import SentenceTransformer
# from langchain_core.documents import Document
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore")

class ArticleGenerator:
    def __init__(self, groq_api_key=None, model_name="Llama3-8b-8192", vector_store_path="vector_db"):
        load_dotenv()  # Load environment variables from .env file
        self.groq_api_key = groq_api_key or os.getenv('GROQ_API_KEY')  # Get Groq API key from argument or environment
        if not self.groq_api_key:
            raise ValueError("Groq API key not provided or found.")
        
        self.llm = ChatGroq(
            groq_api_key=self.groq_api_key,
            model_name=model_name
        )  # Initialize Groq LLM with API key and model name
        self.vector_store = None
        self.vector_store_path = vector_store_path  # Path to save/load FAISS vector store
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")  # Embedding model for semantic search

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
        """)  # Prompt template for article generation

    def load_vector_database(self):
        if not os.path.exists(self.vector_store_path):
            raise FileNotFoundError("Vector store not found. Run setup first.")
        self.vector_store = FAISS.load_local(
            self.vector_store_path,
            self.embeddings,
            allow_dangerous_deserialization=True  # ✅ Enable with caution
        )  # Load FAISS vector store from disk
        print("Vector DB loaded from disk.")

    def generate_article(self, title, num_similar_articles=3):
        if self.vector_store is None:
            raise ValueError("Vector store not loaded. Call load_vector_database() first.")

        start = time.time()  # Start timing

        retriever = self.vector_store.as_retriever(search_kwargs={"k": num_similar_articles})  # Retrieve similar articles
        chain = create_retrieval_chain(retriever, create_stuff_documents_chain(self.llm, self.article_prompt))  # Create retrieval and generation chain
        response = chain.invoke({"input": title})  # Generate article using LLM and similar articles
        duration = time.time() - start  # Calculate generation time

        # print(response)

        return {
            "title": title,
            "article": response["answer"],
            "generation_time_seconds": round(duration, 2)
        }


generator = ArticleGenerator()  # Instantiate the article generator
# generator.load_vector_database()  # Load the vector database
# generator.generate_article("AI in HealthCare", num_similar_articles=3)  # Generate article based on title