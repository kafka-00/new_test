#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# 1. Pull the latest changes from the main branch
echo "Pulling latest changes from GitHub..."
git pull origin main

# 2. Run the Python application
echo "Starting the application..."
python3 main.py

echo "Application closed."
