import pandas as pd
import numpy as np
import tensorflow as tf
import pickle
from tensorflow.keras.preprocessing.sequence import pad_sequences
import warnings
warnings.filterwarnings("ignore")

model = tf.keras.models.load_model('models/nextword_model.h5')
tokenizer = pickle.load(open('models/tokenizer.pkl', 'rb'))
max_seq_len = 30

def greedy_sample(preds):
    """Select the word with the highest probability."""
    return np.argmax(preds)

def generate_next_words(seed_text, model, tokenizer, max_seq_len, num_words=10):
    for _ in range(num_words):
        token_list = tokenizer.texts_to_sequences([seed_text])[0]
        token_list = pad_sequences([token_list], maxlen=max_seq_len - 1, padding='pre')
        predicted_probs = model.predict(token_list, verbose=0)[0]
        next_index = greedy_sample(predicted_probs)
        next_word = tokenizer.index_word.get(next_index, '')
        if next_word == "":
            continue
        seed_text += " " + next_word
    return seed_text

# Example usage
print(generate_next_words("Artificial intelligence is", model, tokenizer, max_seq_len))




