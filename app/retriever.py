import faiss
import pickle
import numpy as np

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

index = faiss.read_index("data/faiss.index")

with open("data/metadata.pkl", "rb") as f:
    metadata = pickle.load(f)


TECH_KEYWORDS = {
    "rust": ["linux", "network", "coding", "programming"],
    "backend": ["java", "sql", "spring", "coding"],
    "java": ["java", "spring", "sql"],
    "python": ["python", "coding"],
    "network": ["networking", "implementation"],
    "cloud": ["aws", "cloud"],
    "aws": ["aws", "cloud"],
    "docker": ["docker", "devops"],
    "frontend": ["javascript", "frontend"],
}


BAD_KEYWORDS = [
    "report",
    "manager report",
    "development report",
    "sales",
    "retail",
    "mining"
]


def search_assessments(query, top_k=20):

    query_embedding = model.encode([query])

    query_embedding = np.array(query_embedding).astype("float32")

    distances, indices = index.search(query_embedding, top_k)

    query_lower = query.lower()

    boosted_terms = []

    for trigger, related in TECH_KEYWORDS.items():

        if trigger in query_lower:

            boosted_terms.extend(related)

    results = []

    for idx in indices[0]:

        if idx >= len(metadata):
            continue

        item = metadata[idx]

        combined_text = " ".join([
            item.get("name", ""),
            item.get("description", ""),
            " ".join(item.get("keys", []))
        ]).lower()

        relevance_score = 0

        # keyword boosting
        for term in boosted_terms:

            if term in combined_text:
                relevance_score += 3

        # direct query overlap
        for word in query_lower.split():

            if word in combined_text:
                relevance_score += 1

        # penalties
        for bad in BAD_KEYWORDS:

            if bad in combined_text:
                relevance_score -= 5

        item["relevance_score"] = relevance_score

        results.append(item)

    results = sorted(
        results,
        key=lambda x: x.get("relevance_score", 0),
        reverse=True
    )

    return results[:8]