#!/bin/bash

echo "Starting all services..."
docker-compose up -d

echo "Initializing database..."
sleep 5  # Wait for the database to initialize
docker exec -i $(docker-compose ps -q db) psql -U user -d translation < db/init.sql

echo "All services are up and running."
