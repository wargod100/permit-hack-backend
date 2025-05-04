from permit import Permit
from dotenv import load_dotenv
import requests
from src.constants import (
    PERMIT_API_URL, PERMIT_PROJECT_ID, PERMIT_ENVIRONMENT_ID,
    PERMIT_API_KEY, PERMIT_PDP_URL, USERS, PERMISSION_TYPES
)

load_dotenv()

print("Loading Permit configuration:")
print(f"PDP URL: {PERMIT_PDP_URL}")
print(f"API Key exists: {'Yes' if PERMIT_API_KEY else 'No'}")

# Initialize Permit client
permit = Permit(
    token=PERMIT_API_KEY,
    pdp=PERMIT_PDP_URL,
)

async def sync_user(username: str):
    """
    Sync a user with Permit.io
    """
    if username not in USERS:
        return False, "Invalid user"
    
    user = USERS[username]
    try:
        # Sync user with Permit.io - only sending required fields
        await permit.api.sync_user({
            "key": user["key"],
            "email": user["email"]
        })
        return True, "User synced successfully"
    except Exception as e:
        print(f"Error syncing user: {str(e)}")
        return False, f"Error syncing user: {str(e)}"

async def check_permission(username: str, permission_name: str) -> tuple[bool, str]:
    """
    Check if a user has a specific permission using Permit
    """
    print(f"\n=== Permission Check Debug ===")
    print(f"Username: {username}")
    print(f"Permission name: {permission_name}")
    print(f"PDP URL: {PERMIT_PDP_URL}")
    print(f"API Key exists: {'Yes' if PERMIT_API_KEY else 'No'}")
    
    if username not in USERS:
        print("User not found in database")
        return False, "Invalid user"
    
    user = USERS[username]
    print(f"\nUser details:")
    print(f"Key: {user['key']}")
    print(f"Email: {user['email']}")
    print(f"Role: {user['role']}")
    
    permission_config = PERMISSION_TYPES.get(permission_name)
    if not permission_config:
        print(f"Unknown permission type: {permission_name}")
        return False, f"Unknown permission type: {permission_name}"
    
    try:
        print("\nPermit check details:")
        print(f"Action: {permission_config['action']}")
        print(f"Resource: {permission_config['resource']}")
        
        # First sync the user
        print("\nSyncing user...")
        sync_success, sync_message = await sync_user(username)
        print(f"Sync result: {sync_message}")
        if not sync_success:
            return False, sync_message
            
        # Try direct permission check
        print("\nAttempting permission check...")
        try:
            # Try with just the key
            allowed = await permit.check(
                user["key"],
                permission_config["action"],
                permission_config["resource"]
            )
            print(f"Permission check result (using key): {allowed}")
            
            if not allowed:
                # Try with email as fallback
                allowed = await permit.check(
                    user["email"],
                    permission_config["action"],
                    permission_config["resource"]
                )
                print(f"Permission check result (using email): {allowed}")
        except Exception as check_error:
            print(f"Permission check error: {str(check_error)}")
            allowed = False
        
        print(f"\nFinal permission result: {allowed}")
        reason = "Permission granted" if allowed else "You don't have permission to perform this action"
        return allowed, reason
        
    except Exception as e:
        print(f"Error in permission check: {str(e)}")
        return False, f"Error checking permissions: {str(e)}"

async def check_action_permission(user_id: str, action_type: str) -> tuple[bool, str]:
    """
    Check if a user has permission for a specific action
    """
    print(f"\nChecking action permission:")
    print(f"User ID: {user_id}")
    print(f"Action type: {action_type}")
    
    if action_type not in PERMISSION_TYPES:
        print(f"Unknown action type: {action_type}")
        return False, f"Unknown action type: {action_type}"
    
    return await check_permission(user_id, action_type)

async def get_permit_users():
    """
    Fetch all users from Permit.io
    """
    try:
        url = f"{PERMIT_API_URL}/v2/facts/{PERMIT_PROJECT_ID}/{PERMIT_ENVIRONMENT_ID}/users"
        headers = {
            "Authorization": f"Bearer {PERMIT_API_KEY}"
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching users: {response.status_code}")
            print(f"Response: {response.text}")
            return {"error": "Failed to fetch users"}
            
    except Exception as e:
        print(f"Error in get_permit_users: {str(e)}")
        return {"error": str(e)}

async def update_user_role(user_id: str, role: str, action: str = "add"):
    """
    Add or remove a role for a user in Permit.io
    """
    try:
        url = f"{PERMIT_API_URL}/v2/facts/{PERMIT_PROJECT_ID}/{PERMIT_ENVIRONMENT_ID}/users/{user_id}/roles"
        headers = {
            "Authorization": f"Bearer {PERMIT_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "role": role,
            "tenant": "default"
        }
        
        if action == "add":
            response = requests.post(url, headers=headers, json=data)
        else:  # remove
            response = requests.delete(url, headers=headers, json=data)
            
        if response.status_code in [200, 201, 204]:
            return {"success": True, "message": f"Role {action}ed successfully"}
        else:
            print(f"Error updating role: {response.status_code}")
            print(f"Response: {response.text}")
            return {"error": f"Failed to {action} role"}
            
    except Exception as e:
        print(f"Error in update_user_role: {str(e)}")
        return {"error": str(e)}