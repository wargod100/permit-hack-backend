#!/bin/bash

# Install Git if not already installed
if ! command -v git &> /dev/null; then
    curl -sL https://deb.nodesource.com/setup_14.x | bash -
    apt-get update
    apt-get install -y git
fi

# Start the application
cd %HOME%\site\wwwroot\server
gunicorn app:app --bind=0.0.0.0:$PORT 