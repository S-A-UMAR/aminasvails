#!/bin/bash
# Create and activate virtual environment to bypass PEP 668 externally-managed-environment
python3 -m venv venv
source venv/bin/activate

# Install requirements inside virtualenv
pip install -r requirements.txt

# Run collectstatic to generate staticfiles directory
python3 manage.py collectstatic --noinput
