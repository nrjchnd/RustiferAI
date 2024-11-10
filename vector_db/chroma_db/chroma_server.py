from flask import Flask, request, jsonify
import chromadb
from chromadb.utils import embedding_functions
import os

app = Flask(__name__)

# Retrieve OpenAI API key from environment variable
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', 'your-openai-api-key')

# Initialize the embedding function
embedding_fn = embedding_functions.OpenAIEmbeddingFunction(api_key=OPENAI_API_KEY)

# Initialize ChromaDB client and collection with the embedding function
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="code_snippets", embedding_function=embedding_fn)

@app.route('/add', methods=['POST'])
def add_document():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        documents = data.get('documents')
        metadatas = data.get('metadatas')
        ids = data.get('ids')

        if not documents or not isinstance(documents, list):
            return jsonify({"error": "No documents provided or invalid format"}), 400

        # Ensure metadatas and ids are lists of the same length as documents
        num_documents = len(documents)

        if metadatas is None:
            metadatas = [{}] * num_documents
        if ids is None:
            ids = [str(i) for i in range(num_documents)]

        if not (len(documents) == len(metadatas) == len(ids)):
            return jsonify({"error": "The lengths of documents, metadatas, and ids must match"}), 400

        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Error in /add endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/query', methods=['POST'])
def query_documents():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        query_text = data.get('query')
        n_results = data.get('n_results', 5)

        if not query_text:
            return jsonify({"error": "No query text provided"}), 400

        # Perform the query
        results = collection.query(query_texts=[query_text], n_results=n_results)

        # Extract documents from results
        # The 'documents' key contains a list of lists of documents
        documents = results.get('documents', [[]])[0]

        return jsonify({"documents": documents}), 200

    except Exception as e:
        print(f"Error in /query endpoint: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Set the port to 8001 as specified
    app.run(host='0.0.0.0', port=8001)
