import os
import time
import json
import psycopg2
import requests
import git
import shutil
import subprocess

from utils.retrieval import get_relevant_context

# Environment variables
DATABASE_URL = os.environ.get('DATABASE_URL')
OLLAMA_API_URL = os.environ.get('OLLAMA_API_URL')
VECTOR_DB_URL = os.environ.get('VECTOR_DB_URL')


def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    try:
        return psycopg2.connect(DATABASE_URL)
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        raise


def clone_repository(repo_url, branch, auth_token, local_path):
    """Clone a Git repository to a local path."""
    try:
        if auth_token:
            # Insert auth token into repo URL
            if 'github.com' in repo_url:
                repo_url = repo_url.replace('https://', f'https://{auth_token}@')
        git.Repo.clone_from(repo_url, local_path, branch=branch)
    except Exception as e:
        print(f"Error cloning repository {repo_url}: {e}")
        raise


def index_repository(repo_path):
    """Traverse the repository and collect metadata of C/C++ files."""
    file_index = []
    try:
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(('.c', '.cpp', '.h')):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, repo_path)
                    stat = os.stat(full_path)
                    file_index.append({
                        'file_path': rel_path,
                        'full_path': full_path,
                        'last_modified': time.ctime(stat.st_mtime),
                        'size': stat.st_size
                    })
        return file_index
    except Exception as e:
        print(f"Error indexing repository at {repo_path}: {e}")
        raise


def store_index_in_db(file_index):
    """Store the file index in the PostgreSQL database."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        for file in file_index:
            cur.execute("""
                INSERT INTO fileindex (file_path, last_modified, size)
                VALUES (%s, %s, %s)
                ON CONFLICT (file_path) DO NOTHING;
            """, (file['file_path'], file['last_modified'], file['size']))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error storing file index in database: {e}")
        raise


def add_documents_to_vector_db(file_index):
    """Add code documents to the vector database for retrieval."""
    documents = []
    metadatas = []
    try:
        for file in file_index:
            with open(file['full_path'], 'r') as f:
                code = f.read()
            documents.append(code)
            metadatas.append({'file_path': file['file_path']})
        payload = {
            'documents': documents,
            'metadatas': metadatas
        }
        response = requests.post(f'{VECTOR_DB_URL}/add', json=payload)
        response.raise_for_status()
        return True
    except (requests.exceptions.RequestException, IOError) as e:
        print(f"Error adding documents to vector DB: {e}")
        return False


def get_pending_files():
    """Retrieve a list of files with status 'pending' from the database."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, file_path FROM fileindex WHERE status = 'pending';
        """)
        files = cur.fetchall()
        cur.close()
        conn.close()
        return files
    except Exception as e:
        print(f"Error retrieving pending files: {e}")
        return []


def update_file_status(file_id, status, error_message=None):
    """Update the status of a file in the database."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE fileindex SET status = %s WHERE id = %s;
        """, (status, file_id))
        if error_message:
            cur.execute("""
                INSERT INTO translationstatus (file_id, error_message)
                VALUES (%s, %s)
                ON CONFLICT (file_id) DO UPDATE SET error_message = EXCLUDED.error_message;
            """, (file_id, error_message))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error updating file status for file ID {file_id}: {e}")
        raise


def translate_code(code, context):
    """Translate C/C++ code to Rust using the Ollama API with context."""
    # Prepare the prompt for code translation with context
    prompt = f"""
You are an AI assistant that translates C/C++ code to idiomatic Rust code. Use the following context to improve your translation:

Context:
{context}

Now, translate the following C/C++ code into Rust:

```c
{code}
"""
    headers = {'Content-Type': 'application/json'}
    payload = {"model": "incept5/llama3.1-claude", "prompt": prompt}
    try:
        response = requests.post(f"{OLLAMA_API_URL}/api/generate", headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()
        translated_code = data.get('response', '')
        if not translated_code:
            print("Received empty response from translation API.")
            return None
        return translated_code.strip()
    except requests.exceptions.RequestException as e:
        print(f"Error during translation API request: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing translation API response: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during translation: {e}")
        return None


def compile_code(code, filename):
    """Compile the translated Rust code to check for syntax errors."""
    temp_dir = '/tmp/translation'
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        # Adjust filename extension to .rs
        filename_rs = filename.replace('.c', '.rs').replace('.cpp', '.rs').replace('.h', '.rs')
        file_path = os.path.join(temp_dir, filename_rs)
        with open(file_path, 'w') as f:
            f.write(code)
        result = subprocess.run(['rustc', file_path], capture_output=True, text=True)
        if result.returncode == 0:
            return True, ''
        else:
            error_msg = result.stderr
            print(f"Compilation error for file {filename_rs}: {error_msg}")
            return False, error_msg
    except Exception as e:
        print(f"Error during compilation of file {filename}: {e}")
        return False, str(e)


def process_files(source_repo_path, dest_repo_path):
    """Process pending files: translate and compile them."""
    files = get_pending_files()
    if not files:
        print("No pending files to process.")
        return
    for file_id, file_path in files:
        update_file_status(file_id, 'in-progress')
        try:
            # Read source code
            full_path = os.path.join(source_repo_path, file_path)
            with open(full_path, 'r') as f:
                code = f.read()
            # Retrieve context
            context = get_relevant_context(code)
            # Translate code
            translated_code = translate_code(code, context)
            if not translated_code:
                update_file_status(file_id, 'error', 'Translation failed or empty response')
                continue
            # Compile code
            compiled, error = compile_code(translated_code, os.path.basename(file_path))
            if not compiled:
                update_file_status(file_id, 'error', f'Compilation failed: {error}')
                continue
            # Write translated code to destination
            dest_file_path = file_path.replace('.c', '.rs').replace('.cpp', '.rs').replace('.h', '.rs')
            dest_full_path = os.path.join(dest_repo_path, dest_file_path)
            os.makedirs(os.path.dirname(dest_full_path), exist_ok=True)
            with open(dest_full_path, 'w') as f:
                f.write(translated_code)
            # Update status
            update_file_status(file_id, 'translated')
        except IOError as e:
            print(f"I/O error processing file {file_path}: {e}")
            update_file_status(file_id, 'error', f'I/O error: {e}')
        except Exception as e:
            print(f"Exception while processing file {file_path}: {e}")
            update_file_status(file_id, 'error', f'Exception: {str(e)}')


def main():
    """Main loop to continuously check for repositories and process files."""
    while True:
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM repositories LIMIT 1;")
            repo_info = cur.fetchone()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error retrieving repository info: {e}")
            time.sleep(10)
            continue

        if repo_info:
            # Extract repository information
            repo_id, source_repo_url, source_branch, source_auth, dest_repo_url, dest_branch, dest_auth = repo_info

            source_repo_path = '/tmp/source_repo'
            dest_repo_path = '/tmp/dest_repo'

            # Clean previous repositories
            if os.path.exists(source_repo_path):
                shutil.rmtree(source_repo_path)
            if os.path.exists(dest_repo_path):
                shutil.rmtree(dest_repo_path)

            try:
                # Clone repositories
                print("Cloning source repository...")
                clone_repository(source_repo_url, source_branch, source_auth, source_repo_path)
                print("Cloning destination repository...")
                clone_repository(dest_repo_url, dest_branch, dest_auth, dest_repo_path)

                # Index source repository
                print("Indexing source repository...")
                file_index = index_repository(source_repo_path)
                store_index_in_db(file_index)

                # Add documents to vector database
                print("Adding documents to vector database...")
                success = add_documents_to_vector_db(file_index)
                if not success:
                    print("Failed to add documents to vector database.")
                    continue

                # Process files
                print("Processing files...")
                process_files(source_repo_path, dest_repo_path)

                # Commit and push changes
                print("Committing and pushing changes to destination repository...")
                repo = git.Repo(dest_repo_path)
                repo.git.add('--all')
                repo.index.commit('Automated translation of C/C++ to Rust')
                origin = repo.remote(name='origin')
                if dest_auth:
                    dest_repo_url_with_auth = dest_repo_url.replace('https://', f'https://{dest_auth}@')
                    origin.set_url(dest_repo_url_with_auth)
                origin.push()
            except Exception as e:
                print(f"Exception during processing: {e}")
            finally:
                # Clean up
                print("Cleaning up temporary files...")
                if os.path.exists(source_repo_path):
                    shutil.rmtree(source_repo_path)
                if os.path.exists(dest_repo_path):
                    shutil.rmtree(dest_repo_path)

            print("Waiting before checking for new repositories...")
            time.sleep(60)  # Wait before checking for new repositories
        else:
            print("No repositories found. Retrying...")
            time.sleep(10)  # Wait before checking again


if __name__ == '__main__':
    main()