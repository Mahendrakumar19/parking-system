#!/bin/bash
# Render.com startup script

# Install dependencies
pip install -r requirements.txt

# Start the Flask application with Gunicorn
cd app && gunicorn --bind 0.0.0.0:$PORT app:app