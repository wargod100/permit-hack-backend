import os
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

load_dotenv()
# Pydantic Models
class ActionOutput(BaseModel):
    action_type: str
    reasoning: str

class GitHubIssueOutput(BaseModel):
    title: str
    description: str
    labels: List[str]

# API URLs and Endpoints
PERMIT_API_URL = "https://api.permit.io"

# Permission Types
PERMISSION_TYPES = {
    "onboarding_query": {
        "action": "read",
        "resource": "onboarding_query"
    },
    "github_issues": {
        "action": "create",
        "resource": "github_issues"
    },
    "code_query": {
        "action": "read",
        "resource": "code_query"
    },
    "create_image": {
        "action": "create",
        "resource": "create_image"
    }
}

# Mock User Database
USERS = {
    "admin": {
        "password": "2025DEVChallenge",
        "email": "admin@donutnaturales.com", 
        "role": "Admin",
        "name": "Admin Admin",
        "key": "Admin",
        "firstName": "Admin",
        "lastName": "Admin"
    },
    "dev1": {
        "password": "2025DEVChallenge",
        "email": "dev1@donutnaturales.com",
        "role": "Developer", 
        "name": "Dev1 Dev1",
        "key": "Dev1",
        "firstName": "Dev1",
        "lastName": "Dev1"
    },
    "newuser": {
        "password": "2025DEVChallenge",
        "email": "dev1@donutnaturales.com",
        "role": "Developer", 
        "name": "Dev1 Dev1",
        "key": "Dev1",
        "firstName": "Dev1",
        "lastName": "Dev1"
    },
    "test1": {
        "password": "2025DEVChallenge",
        "email": "test1@donutnaturales.com",
        "role": "Tester",
        "name": "Test1 Test",
        "key": "Test1", 
        "firstName": "Test1",
        "lastName": "Test"
    },
    "prod": {
        "password": "2025DEVChallenge",
        "email": "pm@donutnaturales.com",
        "role": "ProductManager",
        "name": "Prod Manager",
        "key": "Prod",
        "firstName": "Prod",
        "lastName": "Manager"
    },
    "pm": {
        "password": "2025DEVChallenge",
        "email": "pm@donutnaturales.com",
        "role": "ProductManager",
        "name": "Prod Manager",
        "key": "Prod",
        "firstName": "Prod",
        "lastName": "Manager"
    }
}

# Environment Variables
PERMIT_PROJECT_ID = os.getenv("PERMIT_PROJECT_ID")
PERMIT_ENVIRONMENT_ID = os.getenv("PERMIT_ENVIRONMENT_ID")
PERMIT_API_KEY = os.getenv("PERMIT_API_KEY")
PERMIT_PDP_URL = os.getenv("PERMIT_PDP_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
GITHUB_API_REPO_URL = os.getenv("GITHUB_API_REPO_URL")
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL") 