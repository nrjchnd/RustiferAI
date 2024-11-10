import os
import requests

VECTOR_DB_URL = os.environ.get('VECTOR_DB_URL')

def get_relevant_context(query_text):
    """Retrieve relevant context from the vector database for a given query."""
    payload = {
        'query': query_text
    }
    try:
        response = requests.post(f'{VECTOR_DB_URL}/query', json=payload)
        response.raise_for_status()
        results = response.json()
        contexts = []
        # Assuming results['documents'] contains the retrieved documents
        for doc in results.get('documents', []):
            contexts.append(doc)
        return '\n'.join(contexts)
    except requests.exceptions.RequestException as e:
        print(f"Error during context retrieval: {e}")
        return ''
