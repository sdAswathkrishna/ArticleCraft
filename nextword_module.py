import pandas as pd
import numpy as np
import os
import gc
import pickle
from nltk.tokenize import sent_tokenize
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout
from tensorflow.keras.callbacks import ModelCheckpoint
from tqdm import tqdm

# === Load and preprocess data ===
df = pd.read_pickle('representative_samples/representative_samples.pkl')

all_sentences = []
for doc in df['clean_text']:
    all_sentences.extend(sent_tokenize(doc))

# Filter short sentences
all_sentences = [s for s in all_sentences if len(s.split()) > 3]

# === Tokenization ===
vocab_size = 10000
tokenizer = Tokenizer(num_words=vocab_size, oov_token="<OOV>")
tokenizer.fit_on_texts(all_sentences)

total_words = min(vocab_size, len(tokenizer.word_index)) + 1

# === Generate n-gram sequences ===
input_sequences = []
max_seq_len = 30

for line in tqdm(all_sentences, desc="Generating n-gram sequences"):
    token_list = tokenizer.texts_to_sequences([line])[0]
    for i in range(1, len(token_list)):
        n_gram_seq = token_list[:i + 1]
        input_sequences.append(n_gram_seq)

# === Padding ===
input_sequences = pad_sequences(input_sequences, maxlen=max_seq_len, padding='pre')
X = input_sequences[:, :-1]
y = input_sequences[:, -1]  # Already integer encoded

# === Build LSTM model ===
model = Sequential()
model.add(Embedding(total_words, 128, input_length=max_seq_len - 1))
model.add(LSTM(256, return_sequences=True))
model.add(Dropout(0.2))
model.add(LSTM(128))
model.add(Dense(128, activation='relu'))
model.add(Dropout(0.2))
model.add(Dense(total_words, activation='softmax'))

model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
model.summary()

# === Train ===
model_path = 'models/nextword_model.h5'
os.makedirs('models', exist_ok=True)

checkpoint = ModelCheckpoint(model_path, monitor='loss', save_best_only=True, verbose=1)
model.fit(X, y, epochs=10, batch_size=128, callbacks=[checkpoint], verbose=1)

# === Save tokenizer ===
with open("models/tokenizer.pkl", "wb") as f:
    pickle.dump(tokenizer, f)

# === Prediction Function with Temperature Sampling ===
def sample_with_temperature(preds, temperature=1.0):
    preds = np.asarray(preds).astype('float64')
    preds = np.log(preds + 1e-10) / temperature
    exp_preds = np.exp(preds)
    preds = exp_preds / np.sum(exp_preds)
    return np.random.choice(len(preds), p=preds)

def load_model_and_tokenizer():
    model = load_model("models/nextword_model.h5")
    with open("models/tokenizer.pkl", "rb") as f:
        tokenizer = pickle.load(f)
    return model, tokenizer

def generate_next_words(seed_text, next_words, model, tokenizer, max_seq_len, temperature=1.0):
    for _ in range(next_words):
        token_list = tokenizer.texts_to_sequences([seed_text])[0]
        token_list = pad_sequences([token_list], maxlen=max_seq_len-1, padding='pre')
        predicted = model.predict(token_list, verbose=0)[0]
        next_index = sample_with_temperature(predicted, temperature)
        output_word = tokenizer.index_word.get(next_index, '')
        if output_word == "<OOV>" or output_word == "":
            continue
        seed_text += " " + output_word
    return seed_text

# === Example Usage ===
if __name__ == "__main__":
    model, tokenizer = load_model_and_tokenizer()
    result = generate_next_words("Hello everyone", 10, model, tokenizer, max_seq_len, temperature=0.8)
    print("➡️", result)
