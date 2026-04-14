import os
import chromadb
from pypdf import PdfReader

# Initialize persistent ChromaDB client
DB_PATH = "./friday_db"
chroma_client = chromadb.PersistentClient(path=DB_PATH)

# Get or create a collection for our documents
collection = chroma_client.get_or_create_collection(name="friday_docs")

def ingest_pdf(file_path: str):
    """Reads a PDF, chunks the text, and stores it in the vector DB."""
    try:
        reader = PdfReader(file_path)
        filename = os.path.basename(file_path)
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                # Simple chunking by page for now
                doc_id = f"{filename}_page_{i}"
                
                collection.upsert(
                    documents=[text],
                    metadatas=[{"source": filename, "page": i}],
                    ids=[doc_id]
                )
        return True, f"Successfully ingested {filename}"
    except Exception as e:
        return False, str(e)

def query_documents(query: str, n_results: int = 3):
    """Queries the vector DB for the most relevant chunks."""
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    # Format the results into a single context string
    if not results['documents'] or not results['documents'][0]:
        return ""
        
    context_chunks = []
    for i, doc in enumerate(results['documents'][0]):
        metadata = results['metadatas'][0][i]
        context_chunks.append(f"[Source: {metadata['source']}, Page: {metadata['page']}]\n{doc}")
        
    return "\n\n".join(context_chunks)

def delete_document(filename: str):
    """Deletes all chunks associated with a specific file."""
    # Fetch all records, filter matching filename, and delete by ID.
    res = collection.get()
    
    ids_to_delete = []
    if res['metadatas']:
        for i, meta in enumerate(res['metadatas']):
            if meta and meta.get('source') == filename:
                ids_to_delete.append(res['ids'][i])
            
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
        return True, f"Deleted {len(ids_to_delete)} chunks for {filename}"
    
    return False, "Document not found"
    
def get_all_documents():
    """Returns a list of unique filenames currently in the DB."""
    res = collection.get()
    sources = set()
    if res['metadatas']:
        for meta in res['metadatas']:
            if meta and meta.get('source'):
                sources.add(meta['source'])
    return list(sources)
