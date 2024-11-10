# Automated C/C++ to Rust Translation Pipeline

## Overview

This project provides a reusable, automated pipeline to translate any C/C++ GitHub repository into Rust. It leverages Ollama to run LLMs locally, ensuring data privacy and efficient resource utilization. The pipeline is fully containerized using Docker.

## Prerequisites

- Docker
- Docker Compose
- Git

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/translation-pipeline.git
cd translation-pipeline

source scripts/setup_env.sh
bash scripts/start.sh

Open your web browser and navigate to http://localhost:8000. Fill in the source and destination repository details to start the translation process.

Watch the logs: 
docker-compose logs -f

Access the db if required: 
docker exec -it $(docker-compose ps -q db) psql -U user -d translation

The translated Rust code will be pushed to the destination repository you specified.
Review the generated README.md in the destination repository for compilation instructions

bash scripts/stop.sh


Components
UI Service
Located in the ui/ directory.
Collects user input for repository details.
Worker Service
Located in the worker/ directory.
Handles cloning, indexing, translation, compilation, and pushing code.
Interacts with Ollama for code translation.
Database Service
Uses PostgreSQL.
Stores repository info, file indexing, and translation status.
Ollama Service
Located in the models/ollama/ directory.
Runs LLMs locally to perform code translation.
Exposes API on port 11434.
Version Control Service
Optional GitLab instance provided in vcs/gitlab/.
Can be replaced with any Git server.
Notes
Ensure that the LLMs used comply with their licensing agreements.
Handle all credentials securely.
The pipeline is designed to be extensible and scalable.
Troubleshooting
Services not starting: Ensure Docker and Docker Compose are installed and running.
Database connection errors: Verify that the DATABASE_URL environment variable is correctly set.
Translation errors: Check the logs for the worker service to identify issues.



---

### Additional Considerations**

- **Model Selection in Ollama:**
  - The `translate_code` function in `translate.py` specifies `"model": "llama2"`.
  - Ensure that the Llama 2 model is downloaded and available in Ollama.

- **Downloading Models with Ollama:**
  - Use the Ollama CLI to download models before starting the service.
  - Example:
    ollama pull llama2

- **Entrypoint Script Adjustments:**
  - The `entrypoint.sh` script in the Ollama service ensures the Ollama server starts when the container runs.

---

- **API Usage:**
  - Ollama provides a REST API for interaction.
  - The `translate_code` function in `translate.py` has been updated to use this API, sending prompts and receiving responses accordingly.

- **Security and Privacy:**
  - Running LLMs locally ensures that the source code does not leave the local environment.
  - This is particularly important for proprietary or sensitive codebases.

---

### Testing the Updated Pipeline**

- **Model Availability:**
  - Before running the pipeline, ensure that the required LLMs are available locally in the Ollama service.

- **Sample Repository:**
  - Test the pipeline with a small, open-source C/C++ repository to validate functionality.
  - Check that files are correctly translated, compiled, and pushed to the destination repository.

- **Error Handling:**
  - Monitor logs for any errors during translation or compilation.
  - Adjust the prompts or handling in `translate.py` as necessary to improve translation quality.


**Next Steps:**

1. **Set Up Ollama:**
   - Ensure that Ollama is correctly installed and configured in the Docker environment.
   - Download the necessary LLMs using the Ollama CLI.

2. **Run the Pipeline:**
   - Start the services using the updated `start.sh` script.
   - Use the UI to initiate a translation job.

3. **Monitor and Adjust:**
   - Monitor the translation process.
   - If needed, adjust the translation prompts or model parameters to improve results.

4. **Scale and Optimize:**
   - Consider scaling the worker service if translating large repositories.
   - Optimize resource allocation in Docker to ensure efficient performance.

