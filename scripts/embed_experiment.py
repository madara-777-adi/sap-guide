import numpy as np
from fastembed import TextEmbedding

MODEL_NAME = "BAAI/bge-small-en-v1.5"

SENTENCES = {
    "A": "How do I post a vendor invoice?",
    "B": "Steps to enter a supplier bill in the system",
    "C": "What time does the canteen open?",
    "D": "MIRO",
    "E": "invoice verification",
}


def cosine(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y)))


def main() -> None:
    model = TextEmbedding(MODEL_NAME)  # first run downloads the model
    keys = list(SENTENCES)
    vectors = dict(zip(keys, model.embed(list(SENTENCES.values()))))

    print(f"Model: {MODEL_NAME}")
    print(f"Vector length: {len(vectors['A'])}")
    print(f"A vs B (same meaning, different words): {cosine(vectors['A'], vectors['B']):.3f}")
    print(f"A vs C (unrelated):                      {cosine(vectors['A'], vectors['C']):.3f}")
    print(f"D vs E (MIRO vs its plain-English name): {cosine(vectors['D'], vectors['E']):.3f}")


if __name__ == "__main__":
    main()