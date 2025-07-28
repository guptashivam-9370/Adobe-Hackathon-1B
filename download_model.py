# download_model.py
from sentence_transformers import SentenceTransformer
from transformers import pipeline
def main():
    """Downloads and saves the sentence transformer model."""
    print("Downloading sentence-transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    model.save('./sbert_model')
    print("Model downloaded and saved to ./sbert_model")
if __name__ == "__main__":
    main()