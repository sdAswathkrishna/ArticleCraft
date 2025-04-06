import pandas as pd
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

class GPT2TextGenerator:
    def __init__(self, csv_path, sample_size=None):
        """
        Initialize the GPT-2 text generation system
        
        Parameters:
        -----------
        csv_path : str
            Path to the CSV file containing cleaned article data
        sample_size : int, optional
            Number of articles to sample (use None to use all data)
        """
        self.csv_path = csv_path
        self.sample_size = sample_size
        self.data = None
        self.gpt2_model = None
        self.gpt2_tokenizer = None
        
        print("Initializing GPT-2 Text Generation System...")
        self.load_data()
        self.load_gpt2_model()
    
    def load_data(self):
        """Load cleaned data from CSV file"""
        print(f"Loading data from {self.csv_path}...")
        try:
            # Read dataset (assuming it's already cleaned)
            full_data = pd.read_csv(self.csv_path)
            
            # Sample a subset if specified
            if self.sample_size and len(full_data) > self.sample_size:
                self.data = full_data.sample(self.sample_size, random_state=42)
                print(f"Sampled {self.sample_size} articles from dataset of {len(full_data)} articles.")
            else:
                self.data = full_data
                print(f"Using all {len(self.data)} articles in dataset.")
                
            # Check if required columns exist
            required_columns = ['title', 'text']
            for col in required_columns:
                if col not in self.data.columns:
                    raise ValueError(f"Required column '{col}' not found in CSV file.")
            
            print(f"Data loaded successfully with {len(self.data)} articles.")
            
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            raise
    
    def load_gpt2_model(self):
        """Load pre-trained GPT-2 model for text generation"""
        print("Loading GPT-2 model...")
        try:
            self.gpt2_tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
            self.gpt2_model = GPT2LMHeadModel.from_pretrained('gpt2')
            
            # Use GPU if available
            if torch.cuda.is_available():
                self.gpt2_model.to('cuda')
                print("GPT-2 model loaded on GPU.")
            else:
                print("GPU not available, using CPU for GPT-2 model.")
                
            print("GPT-2 model loaded successfully.")
            
        except Exception as e:
            print(f"Error loading GPT-2 model: {str(e)}")
            raise
    
    def find_similar_title(self, input_title, top_n=1):
        """Find articles with similar titles using simple word overlap"""
        # Simple word overlap similarity
        input_words = set(input_title.lower().split())
        
        # Calculate title similarity
        self.data['title_similarity'] = self.data['title'].apply(
            lambda x: len(set(x.lower().split()) & input_words) / 
                    max(len(input_words | set(x.lower().split())), 1)
        )
        
        # Return top matching articles
        return self.data.nlargest(top_n, 'title_similarity')
    
    def generate_article(self, input_title, max_length=500, use_similar_article_context=True):
        """Generate article based on input title using GPT-2"""
        print(f"Generating article for title: '{input_title}'")
        
        try:
            # Create base prompt from input title
            prompt = f"Title: {input_title}\n\nArticle: "
            
            # Optionally enhance the prompt with similar article context
            if use_similar_article_context:
                similar_article = self.find_similar_title(input_title, top_n=1)
                if not similar_article.empty:
                    # Get first few sentences of the similar article (up to 100 chars)
                    context = similar_article.iloc[0]['text'][:100] + "..."
                    prompt = f"Title: {input_title}\n\nContext: {context}\n\nArticle: "
            
            # Tokenize prompt
            inputs = self.gpt2_tokenizer(prompt, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = inputs.to('cuda')
            
            # Generate text
            outputs = self.gpt2_model.generate(
                inputs['input_ids'],
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.8,  # Control randomness (higher = more random)
                top_p=0.9,        # Nucleus sampling
                do_sample=True,   # Sample instead of greedy decoding
                no_repeat_ngram_size=2,  # Avoid repeating the same n-grams
                pad_token_id=self.gpt2_tokenizer.eos_token_id
            )
            
            # Decode generated text
            generated_text = self.gpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove the prompt from the generated text
            article_text = generated_text.replace(prompt, "")
            
            return article_text
            
        except Exception as e:
            print(f"Error during GPT-2 generation: {str(e)}")
            similar_articles = self.find_similar_title(input_title)
            
            if not similar_articles.empty:
                print("Falling back to similar article retrieval...")
                return similar_articles.iloc[0]['text']
            else:
                return "Could not generate article due to an error."

# Example usage
if __name__ == "__main__":
    # Path to your cleaned CSV file
    csv_path = "final_nlp_data.csv"
    
    # Initialize generator
    generator = GPT2TextGenerator(csv_path, sample_size=1000)
    
    # Generate an article based on user input title
    user_title = "The Impact of Artificial Intelligence on Modern Healthcare"
    generated_article = generator.generate_article(
        user_title, 
        max_length=1000, 
        use_similar_article_context=True
    )
    
    print("\n" + "="*50)
    print(f"Generated Article for: '{user_title}'")
    print("="*50)
    print(generated_article[:1000] + "..." if len(generated_article) > 1000 else generated_article)
    
    # Save the generated article to a file
    with open("generated_article.txt", "w", encoding="utf-8") as f:
        f.write(f"Title: {user_title}\n\n")
        f.write(generated_article)
    
    print("\nGenerated article saved to 'generated_article.txt'")