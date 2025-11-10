"""Get Auth0 access token for testing."""
import requests
import json

# Your Auth0 credentials from .env
AUTH0_DOMAIN = "dev-jbrriuc5vyjmiwtx.us.auth0.com"
AUTH0_CLIENT_ID = "eh3lkyPjejB7dngFewuGp6FSP1l6j39D"

# IMPORTANT: This should be your API identifier, NOT the userinfo endpoint
# Set this in Auth0: Applications → APIs → Create API or use existing API identifier
AUTH0_AUDIENCE = "https://magicminds-api"  # Your API identifier

# Test user credentials (create this user in Auth0 dashboard first)
# Go to https://manage.auth0.com → Users → Create User
USERNAME = "test@example.com"
PASSWORD = "TestPass123!"

def get_token():
    """Get Auth0 access token using Resource Owner Password Grant."""
    url = f"https://{AUTH0_DOMAIN}/oauth/token"
    
    # Try with password-realm grant type (more reliable)
    payload = {
        "grant_type": "http://auth0.com/oauth/grant-type/password-realm",
        "username": USERNAME,
        "password": PASSWORD,
        "client_id": AUTH0_CLIENT_ID,
        "audience": AUTH0_AUDIENCE,
        "scope": "openid profile email",
        "realm": "Username-Password-Authentication"
    }
    
    headers = {"content-type": "application/json"}
    
    print(f"🔐 Requesting token from Auth0...")
    print(f"Domain: {AUTH0_DOMAIN}")
    print(f"Username: {USERNAME}")
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        print("\n✅ Token obtained successfully!")
        print(f"\nAccess Token:\n{access_token}\n")
        print(f"Token Type: {token_data.get('token_type')}")
        print(f"Expires In: {token_data.get('expires_in')} seconds")
        
        # Save token to file
        with open("auth_token.txt", "w") as f:
            f.write(access_token)
        print("\n💾 Token saved to auth_token.txt")
        
        # Show how to use it
        print("\n📝 Usage:")
        print(f'  PowerShell: $TOKEN = Get-Content auth_token.txt')
        print(f'  cURL: curl -H "Authorization: Bearer $(Get-Content auth_token.txt)" ...')
        
        return access_token
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 403:
            print("\n⚠️  Password grant might not be enabled.")
            print("Enable it in Auth0:")
            print("1. Go to https://manage.auth0.com")
            print("2. Applications → Your App → Settings")
            print("3. Advanced Settings → Grant Types")
            print("4. Enable 'Password'")
            print("5. Save Changes")
        elif response.status_code == 401:
            print("\n⚠️  Invalid credentials.")
            print("Create a test user in Auth0:")
            print("1. Go to https://manage.auth0.com")
            print("2. User Management → Users → Create User")
            print(f"3. Email: {USERNAME}")
            print(f"4. Password: {PASSWORD}")
        
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("Auth0 Token Generator - MagicMinds API")
    print("=" * 60)
    
    # Check if requests is installed
    try:
        import requests
    except ImportError:
        print("\n❌ 'requests' library not found.")
        print("Install it: pip install requests")
        exit(1)
    
    token = get_token()
    
    if token:
        print("\n" + "=" * 60)
        print("✅ Ready to test the API!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Make sure API is running: uvicorn app.main:app --reload --port 8080")
        print("2. Test with: python test_api.py")
        print("3. Or use Swagger UI: http://localhost:8080/docs")
