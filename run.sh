#!/bin/bash
echo "Starting University Parking Management System..."
echo
echo "Installing dependencies..."
pip install -r requirements.txt
echo
echo "Starting the application..."
cd app
python app.py