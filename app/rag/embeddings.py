from typing import List
from fastembed import TextEmbedding

MODEL_NAME = "BAAI/bge-small-en-v1.5"
print(f" Loading embedding model ({MODEL_NAME}) via fastembed (ONNX runtime, low-memory)...")
model = TextEmbedding(model_name=MODEL_NAME)
print(" Embedding model loaded successfully.")

BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def create_embeddings(texts: List[str], is_query: bool = False) -> List[List[float]]:
    """
    Generates L2-normalized dense vector embeddings for input text strings.
    Same model, same output shape as before — only the runtime changed
    (ONNX via fastembed instead of PyTorch via sentence-transformers),
    specifically to fix an out-of-memory crash on the 512MB deploy target.

    :param texts: List of strings to encode.
    :param is_query: Set to True when encoding user search queries to prepend BGE query instruction.
    """
    if is_query:
        texts = [f"{BGE_QUERY_PREFIX}{text}" for text in texts]

    embeddings = list(model.embed(texts))
    return [e.tolist() for e in embeddings]