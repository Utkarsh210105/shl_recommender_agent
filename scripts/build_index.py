import json
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

with open("data/catalog.json", "r", encoding="utf-8") as f:
    catalog = json.load(f)

documents = []

for item in catalog:

    text = f"""
    Name: {item.get('name', '')}

    Description: {item.get('description', '')}

    Job Levels: {", ".join(item.get('job_levels', []))}

    Languages: {", ".join(item.get('languages', []))}

    Duration: {item.get('duration', '')}

    Keys: {", ".join(item.get('keys', []))}

    Adaptive: {item.get('adaptive', '')}

    Remote: {item.get('remote', '')}
    """

    documents.append(text)

embeddings = model.encode(documents)

embeddings = np.array(embeddings).astype("float32")

dimension = embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)

index.add(embeddings)

faiss.write_index(index, "data/faiss.index")

with open("data/metadata.pkl", "wb") as f:
    pickle.dump(catalog, f)

print("FAISS index built successfully.")