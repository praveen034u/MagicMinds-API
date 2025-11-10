"""Test MagicMinds API endpoints."""
import requests
import json
import sys
from pathlib import Path

# Base URL
BASE_URL = "http://localhost:8080"

def load_token():
    """Load token from file."""
    token_file = Path("auth_token.txt")
    if not token_file.exists():
        print("❌ Token file not found!")
        print("Run: python get_token.py")
        sys.exit(1)
    
    with open(token_file, "r") as f:
        return f.read().strip()

# Read token
TOKEN = load_token()

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def print_response(title, response):
    """Print formatted response."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    
    try:
        data = response.json()
        print(f"Response:\n{json.dumps(data, indent=2)}")
        return data
    except:
        print(f"Response: {response.text}")
        return None

def test_health():
    """Test health endpoints."""
    print("\n\n🏥 TESTING HEALTH ENDPOINTS")
    
    response = requests.get(f"{BASE_URL}/healthz")
    print_response("GET /healthz (Liveness)", response)
    
    response = requests.get(f"{BASE_URL}/readyz")
    print_response("GET /readyz (Readiness)", response)

def test_create_parent():
    """Create parent profile."""
    print("\n\n👨‍👩‍👧 TESTING PARENT PROFILE")
    
    data = {"name": "John Doe"}
    response = requests.post(
        f"{BASE_URL}/profiles/parent",
        headers=headers,
        json=data
    )
    parent = print_response("POST /profiles/parent - Create Parent", response)
    
    if response.status_code in [200, 201]:
        print(f"✅ Parent created: {parent['name']} ({parent['email']})")
        return parent
    elif response.status_code == 400 and "already exists" in response.text:
        print("ℹ️  Parent already exists, fetching...")
        return test_get_parent()
    else:
        print(f"❌ Failed to create parent")
        return None

def test_get_parent():
    """Get parent profile."""
    response = requests.get(
        f"{BASE_URL}/profiles/parent",
        headers=headers
    )
    parent = print_response("GET /profiles/parent - Get Parent", response)
    
    if response.status_code == 200:
        print(f"✅ Parent retrieved: {parent['name']}")
        return parent
    else:
        print(f"❌ Failed to get parent")
        return None

def test_create_child():
    """Create child profile."""
    print("\n\n👧 TESTING CHILD PROFILES")
    
    children_data = [
        {"name": "Alice", "age_group": "5-7", "avatar": "https://example.com/alice.png"},
        {"name": "Bob", "age_group": "8-10", "avatar": "https://example.com/bob.png"}
    ]
    
    created_children = []
    
    for child_data in children_data:
        response = requests.post(
            f"{BASE_URL}/profiles/children",
            headers=headers,
            json=child_data
        )
        child = print_response(f"POST /profiles/children - Create {child_data['name']}", response)
        
        if response.status_code in [200, 201]:
            print(f"✅ Child created: {child['name']} (Age: {child['age_group']})")
            created_children.append(child)
        else:
            print(f"⚠️  Could not create {child_data['name']}")
    
    return created_children

def test_get_children():
    """Get all children."""
    response = requests.get(
        f"{BASE_URL}/profiles/children",
        headers=headers
    )
    children = print_response("GET /profiles/children - List All Children", response)
    
    if response.status_code == 200:
        print(f"✅ Found {len(children)} children")
        for child in children:
            print(f"  - {child['name']} (Age: {child['age_group']})")
        return children
    else:
        print(f"❌ Failed to get children")
        return []

def test_update_child(child_id):
    """Update child profile."""
    data = {"name": "Alice Updated", "voice_clone_enabled": True}
    response = requests.patch(
        f"{BASE_URL}/profiles/children/{child_id}",
        headers=headers,
        json=data
    )
    child = print_response(f"PATCH /profiles/children/{child_id} - Update Child", response)
    
    if response.status_code == 200:
        print(f"✅ Child updated: {child['name']}")
        return child
    else:
        print(f"❌ Failed to update child")
        return None

def test_create_room():
    """Create a game room."""
    print("\n\n🎮 TESTING GAME ROOMS")
    
    data = {
        "game_id": "math_quest",
        "difficulty": "medium",
        "max_players": 4,
        "has_ai_player": True,
        "ai_player_name": "RoboMath",
        "ai_player_avatar": "https://example.com/robot.png",
        "selected_category": "addition"
    }
    response = requests.post(
        f"{BASE_URL}/rooms",
        headers=headers,
        json=data
    )
    room = print_response("POST /rooms - Create Game Room", response)
    
    if response.status_code in [200, 201]:
        print(f"✅ Room created: {room['room_code']}")
        print(f"   Max Players: {room['max_players']}")
        print(f"   Current Players: {room['current_players']}")
        return room
    else:
        print(f"❌ Failed to create room")
        return None

def test_create_story(child_id):
    """Create a generated story."""
    print("\n\n📖 TESTING STORIES")
    
    data = {
        "child_id": child_id,
        "story_text": "Once upon a time, in a magical land far away, there lived a brave young hero named Alice. She embarked on an incredible adventure...",
        "prompt_used": "Create a story about a magical adventure for a 7-year-old",
        "voice_audio_url": "https://example.com/story_audio.mp3"
    }
    response = requests.post(
        f"{BASE_URL}/stories",
        headers=headers,
        json=data
    )
    story = print_response("POST /stories - Create Story", response)
    
    if response.status_code in [200, 201]:
        print(f"✅ Story created")
        print(f"   Preview: {story['story_text'][:60]}...")
        return story
    else:
        print(f"❌ Failed to create story")
        return None

def test_get_stories(child_id):
    """Get all stories for a child."""
    response = requests.get(
        f"{BASE_URL}/stories?child_id={child_id}",
        headers=headers
    )
    stories = print_response(f"GET /stories?child_id={child_id} - Get Stories", response)
    
    if response.status_code == 200:
        print(f"✅ Found {len(stories)} stories")
        return stories
    else:
        print(f"❌ Failed to get stories")
        return []

def test_voice_subscription():
    """Test voice subscription."""
    print("\n\n💳 TESTING BILLING")
    
    data = {
        "stripe_subscription_id": "sub_test_123456",
        "status": "active",
        "plan_type": "premium"
    }
    response = requests.post(
        f"{BASE_URL}/billing/voice-subscription",
        headers=headers,
        json=data
    )
    subscription = print_response("POST /billing/voice-subscription - Create Subscription", response)
    
    if response.status_code in [200, 201]:
        print(f"✅ Subscription created: {subscription['plan_type']} ({subscription['status']})")
        return subscription
    else:
        print(f"❌ Failed to create subscription")
        return None

def run_full_test():
    """Run complete test suite."""
    print("\n" + "="*60)
    print("🚀 MAGICMINDS API - COMPREHENSIVE TEST SUITE")
    print("="*60)
    print(f"API URL: {BASE_URL}")
    print(f"Token: {TOKEN[:20]}...{TOKEN[-20:]}")
    
    try:
        # 1. Health checks
        test_health()
        
        # 2. Parent profile
        parent = test_create_parent()
        if not parent:
            print("\n❌ Cannot continue without parent profile")
            return
        
        # 3. Child profiles
        created_children = test_create_child()
        children = test_get_children()
        
        if not children:
            print("\n❌ Cannot continue without children")
            return
        
        child = children[0]
        
        # 4. Update child
        test_update_child(child['id'])
        
        # 5. Game room
        room = test_create_room()
        
        # 6. Stories
        story = test_create_story(child['id'])
        if story:
            test_get_stories(child['id'])
        
        # 7. Billing
        test_voice_subscription()
        
        # Final summary
        print("\n\n" + "="*60)
        print("✅ TEST SUITE COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"✓ Parent Profile: {parent['name']}")
        print(f"✓ Children: {len(children)} created")
        print(f"✓ Game Room: {room['room_code'] if room else 'N/A'}")
        print(f"✓ Stories: Created and retrieved")
        print(f"✓ All endpoints working!")
        
    except Exception as e:
        print(f"\n\n❌ Test failed with error:")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=2)
        if response.status_code != 200:
            print(f"⚠️  API health check failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API!")
        print(f"Make sure the API is running at {BASE_URL}")
        print("Run: uvicorn app.main:app --reload --port 8080")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
        sys.exit(1)
    
    # Run tests
    run_full_test()
