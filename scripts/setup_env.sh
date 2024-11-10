#!/bin/bash

export DATABASE_URL=postgresql://user:password@db:5432/translation
export OLLAMA_API_URL=http://ollama:11434
export VECTOR_DB_URL=http://vector_db:8001
export OPENAI_API_KEY=${OPENAI_API_KEY}