import requests
import openai
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from gitingest import ingest
from src.constants import (
    OPENAI_API_KEY, PINECONE_API_KEY, GITHUB_API_KEY,
    GITHUB_API_REPO_URL, GITHUB_REPO_URL
)

def callApi(method, url, data, api_key):
    return requests.request(
        method=method,
        url=url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json=data
    )

def initialize_clients():
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY environment variable is not set")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
        
    openai.api_key = OPENAI_API_KEY
    pc = Pinecone(api_key=PINECONE_API_KEY)
    embeddings = OpenAIEmbeddings()
    return pc, embeddings

def process_onboarding_response(query, results):
    context = "\n\n".join([
        f"Section: {result['section']}\n{result['content']}"
        for result in results
    ])
    
    prompt = f"""Provide a clear and direct response about company policies. Focus on delivering information in a well-structured format.

Question: {query}

Here is the relevant information from our knowledge base:
{context}

Guidelines for response:
1. Start directly with the main information - no greetings or signatures needed
2. Use clear headings and bullet points
3. Keep explanations concise but complete
4. Use markdown formatting for better readability
5. Include specific numbers, deadlines, and requirements where relevant
6. Organize information in a logical hierarchy

Example format:
## Main Policy
- Key point 1
- Key point 2

## Requirements
- Requirement 1
- Requirement 2

## Additional Information
- Note 1
- Note 2"""

    response = openai.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are a direct and efficient policy information system. Provide clear, structured information without any fluff or unnecessary formalities."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content

def preprocess_github_issue(query):
    prompt = f"""Format this request into a proper GitHub issue. 
    Create a clear title, detailed description, and appropriate labels.
    The response should be in JSON format with the following structure:
    {{
        "title": "Clear, concise title",
        "description": "Detailed description with context and requirements",
        "labels": ["appropriate", "labels"]
    }}
    
    Original request: {query}
    
    Consider:
    1. Make the title clear and descriptive
    2. Add context in the description
    3. Include any relevant technical details
    4. Add appropriate labels (bug, feature, enhancement, etc.)
    5. Format the description with markdown if needed
    """
    
    response = openai.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are a GitHub issue formatting assistant. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    try:
        response_text = response.choices[0].message.content
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        import json
        issue_data = json.loads(response_text)
        return issue_data
    except Exception as e:
        return {
            "title": query,
            "description": f"Auto-generated issue from query: {query}",
            "labels": ["needs-triage"]
        }

def create_image(prompt, n=1, size="1024x1024"):
    try:
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=n,
            size=size,
            response_format="b64_json"
        )
        
        return {
            "data": [{
                "b64_json": image.b64_json,
                "revised_prompt": image.revised_prompt
            } for image in response.data]
        }
        
    except Exception as e:
        return {"error": str(e)}

def create_github_issue(query):
    issue_data = preprocess_github_issue(query)
    
    data = {
        "title": issue_data["title"],
        "body": issue_data["description"],
        "labels": issue_data["labels"],
        "assignees": []
    }
    
    response = callApi("POST", GITHUB_API_REPO_URL, data, GITHUB_API_KEY)
    return response.json()

def fetch_onboarding_data(query, top_k=5):
    try:
        pc, embeddings = initialize_clients()
        index = pc.Index("onboarding-index")
        query_embedding = embeddings.embed_query(query)
        
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        formatted_results = []
        for match in results['matches']:
            formatted_results.append({
                'content': match.metadata['text'],
                'section': f"{match.metadata['section_number']}. {match.metadata['section_title']}" if match.metadata.get('section_number') else 'General',
                'relevance_score': match.score
            })
        
        processed_response = process_onboarding_response(query, formatted_results)
        
        return {
            'query': query,
            'response': processed_response,
            'source': 'Donut Naturales Onboarding Guide'
        }
        
    except Exception as e:
        return {
            'query': query,
            'error': 'Failed to fetch onboarding information',
            'details': str(e)
        }

def process_repo_query(query, repo_data):
    prompt = f"""Analyze this codebase information and provide a clear, structured response.

Question: {query}

Repository Information:
{repo_data}

Guidelines for response:
1. Provide a clear overview of the codebase structure
2. Highlight key files and their purposes
3. Explain relevant code patterns and architecture
4. Use markdown formatting for better readability
5. Include specific technical details where relevant
6. Organize information logically

Format the response with appropriate sections like:

## Repository Overview
- Key details about the repository

## Code Structure
- Main directories and their purposes
- Key files and their roles

## Technical Details
- Important implementation details
- Dependencies and versions

## Relevant Code Patterns
- Notable patterns or practices used"""

    response = openai.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are a technical documentation expert. Analyze codebases and provide clear, structured explanations."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content

def get_repo_context(query):
    if not GITHUB_REPO_URL:
        return {"error": "GitHub repo URL not configured"}
    
    try:
        repo_data = ingest(GITHUB_REPO_URL)
        processed_response = process_repo_query(query, repo_data)
        return {
            "data": processed_response,
            "raw_data": repo_data
        }
    except Exception as e:
        return {"error": f"Error accessing repository: {str(e)}"}

def classify_action_with_ai(query: str) -> str:
    prompt = f"""Classify this user query into one of the following action types:
    1. onboarding_query - For questions about company policies, procedures, or general information
    2. github_issues - For bug reports, feature requests, or any development tasks
    3. code_query - For questions about code implementation, architecture, or codebase
    4. create_image - For requests to generate or create donut images

    The response should be ONLY the action type (one of: onboarding_query, github_issues, code_query, create_image)

    User Query: {query}

    Consider:
    - Is this about company policies or procedures? → onboarding_query
    - Is this about bugs, features, or tasks? → github_issues
    - Is this about code or implementation? → code_query
    - Is this about generating or creating donuts? → create_image

    Response (just the action type):"""

    response = openai.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are an action classifier. Respond ONLY with the exact action type, no explanation or additional text."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    
    action_type = response.choices[0].message.content.strip().lower()
    valid_types = {"onboarding_query", "github_issues", "code_query", "create_image"}
    
    return action_type if action_type in valid_types else "onboarding_query"


