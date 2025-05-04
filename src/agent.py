from typing import Dict, Any
from src.agent_functions import (
    fetch_onboarding_data,
    create_github_issue,
    get_repo_context,
    classify_action_with_ai,
    create_image
)
from src.permissions import check_action_permission


def analyze_and_summarize_content(content_lines, query):
    """Analyze content and provide a natural, organized summary"""
    # Identify main topics from the content
    topics = {}
    current_topic = "General"
    
    for line in content_lines:
        # Check if line is a section header
        if line.isupper() or (len(line) > 0 and line[0].isdigit() and '.' in line):
            current_topic = line
            topics[current_topic] = []
        else:
            if current_topic not in topics:
                topics[current_topic] = []
            topics[current_topic].append(line)
    
    # Generate a natural response based on the query and content
    response_parts = [
        f"Let me help you understand {query.lower().strip('?.')}.",
        ""
    ]
    
    # Analyze the content and provide a summary
    main_points = []
    details = {}
    
    for topic, points in topics.items():
        if points:  # Only process non-empty topics
            # Clean up points and remove duplicates
            unique_points = list(set([p.strip() for p in points if p.strip()]))
            
            # Identify if this is a main point or detail
            if len(unique_points) <= 2 or any(keyword in topic.lower() for keyword in ['overview', 'summary', 'introduction']):
                main_points.extend(unique_points)
            else:
                details[topic] = unique_points
    
    # Add main points if any
    if main_points:
        response_parts.extend([
            "Here are the key points:",
            *[f"• {point}" for point in main_points],
            ""
        ])
    
    # Add detailed sections
    for topic, points in details.items():
        # Clean up the topic name
        clean_topic = topic.strip().strip('1234567890.').strip()
        if clean_topic:
            response_parts.extend([
                f"## {clean_topic}",
                *[f"• {point}" for point in points],
                ""
            ])
    
    # Add a summary of important procedures or notes if present
    procedures = [p for topic, points in details.items() for p in points if 'procedure' in p.lower() or 'submit' in p.lower()]
    if procedures:
        response_parts.extend([
            "## Important Procedures",
            *[f"• {proc}" for proc in procedures],
            ""
        ])
    
    return "\n".join(response_parts)

def format_onboarding_response(result):
    """Format onboarding query results into a user-friendly response"""
    return result.get('error', f"I apologize, but I encountered an error while searching the onboarding documents: {result['error']}") if 'error' in result else result['response']

def format_github_issue_response(result):
    """Format GitHub issue creation results into a user-friendly response"""
    return f"I apologize, but I encountered an error while creating the GitHub issue: {result['error']}" if 'error' in result else f"I've created a new GitHub issue:\nTitle: {result['title']}\nURL: {result['html_url']}"

def format_image_gen_response(result):
    """Format image generation results into a user-friendly response with displayable image data"""
    if 'error' in result:
        return {
            "message": f"I apologize, but I encountered an error while generating the image: {result['error']}",
            "images": []
        }
    
    if not result or 'data' not in result or not result['data']:
        return {
            "message": "I apologize, but no images were generated successfully.",
            "images": []
        }

    # Get the first image data and its revised prompt
    image_data = result['data'][0]
    revised_prompt = image_data.get('revised_prompt', '')
    
    # Format response with both message and image data
    return {
        "message": f"I've generated a delicious donut based on your request! Here's how I interpreted it: {revised_prompt}",
        "images": [
            {
                "type": "image",
                "format": "base64",
                "data": image_data['b64_json']
            }
        ]
    }

def format_repo_query_response(result):
    """Format repository query results into a user-friendly response"""
    return f"I apologize, but I encountered an error while querying the repository: {result['error']}" if 'error' in result else f"Here's what I found in the codebase:\n{result['data']}"

async def process_query(user_id: str, query: str) -> Dict[str, Any]:
    """Process a user query after checking permissions"""
    action_type = classify_action_with_ai(query)
    
    # Check permissions
    has_permission, reason = await check_action_permission(user_id, action_type)
    if not has_permission:
        return {
            "status": "error",
            "message": reason,
            "action_type": action_type
        }
    
    try:
        action_handlers = {
            "onboarding_query": (fetch_onboarding_data, format_onboarding_response, "text"),
            "github_issues": (create_github_issue, format_github_issue_response, "text"),
            "repo_query": (get_repo_context, format_repo_query_response, "text"),
            "create_image": (create_image, format_image_gen_response, "image")
        }
        
        if action_type not in action_handlers:
            return {
                "status": "error",
                "message": f"Unknown action type: {action_type}"
            }
            
        handler_func, formatter_func, response_type = action_handlers[action_type]
        result = handler_func(query)
        formatted_response = formatter_func(result)
            
        return {
            "status": "success",
            "action_type": action_type,
            "response_type": response_type,
            "response": formatted_response
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "action_type": action_type
        }

