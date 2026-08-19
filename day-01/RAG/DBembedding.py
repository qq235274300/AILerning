from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

def get_embeddings(texts, model="text-embedding-3-small", batch_size=64):
    embeddings = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]

        data = client.embeddings.create(
            input=batch,
            model=model
        ).data

        embeddings.extend([x.embedding for x in data])

    return embeddings

def get_document_embeddings(documents, model="text-embedding-3-small"):
    texts = [
        document["page_content"]
        for document in documents
    ]
    return get_embeddings(texts, model=model)