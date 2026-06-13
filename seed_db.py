import chromadb
from chromadb.utils import embedding_functions

def seed_db():
    client = chromadb.PersistentClient(path="./gigguard.db")
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name="legal_knowledge_base",
        embedding_function=embedding_fn
    )
    
    docs = [
        "Swiggy. account deactivation. no notice provided. no appeal offered. earnings withheld: 3200 INR. reason given: NO_REASON_PROVIDED. Under Code on Social Security 2020, gig workers must be given a 14-day notice before deactivation.",
        "Unjustified withholding of gig worker earnings without an appeal process violates the Fair Platform Work Guidelines 2021.",
        "Platforms can reduce worker pay or change rate cards dynamically based on market conditions, as long as it does not fall below minimum wage.",
        "Zone assignments are purely at the discretion of the platform algorithm and no specific zone is guaranteed by law."
    ]
    
    metadatas = [
        {"id": "doc1", "source": "Code on Social Security 2020", "section": "Section 14"},
        {"id": "doc2", "source": "Fair Platform Work Guidelines 2021", "section": "Section 3(a)"},
        {"id": "doc3", "source": "Code on Wages 2019", "section": "Section 9"},
        {"id": "doc4", "source": "Platform Terms of Service Precedents", "section": "Case Law 2022"}
    ]
    
    ids = ["doc1", "doc2", "doc3", "doc4"]
    
    collection.upsert(
        documents=docs,
        metadatas=metadatas,
        ids=ids
    )
    print(f"ChromaDB seeded with {collection.count()} documents.")

if __name__ == "__main__":
    seed_db()
