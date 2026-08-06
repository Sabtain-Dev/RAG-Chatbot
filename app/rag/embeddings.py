from typing import List
from sentence_transformers import SentenceTransformer

# Load embedding model globally (downloads once on first execution)
MODEL_NAME = "BAAI/bge-small-en-v1.5"
print(f" Loading embedding model ({MODEL_NAME})...")
model = SentenceTransformer(MODEL_NAME)
print(" Embedding model loaded successfully.")

# BGE models require an instruction prefix for query embeddings
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def create_embeddings(texts: List[str], is_query: bool = False) -> List[List[float]]:
    """
    Generates L2-normalized dense vector embeddings for input text strings.
    
    :param texts: List of strings to encode.
    :param is_query: Set to True when encoding user search queries to prepend BGE query instruction.
    """
    if is_query:
        texts = [f"{BGE_QUERY_PREFIX}{text}" for text in texts]

    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()