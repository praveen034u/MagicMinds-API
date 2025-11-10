# API Quick Reference - Updated Endpoints

## 🎯 Key Behavior Changes

### Profiles
- **`POST /profiles/parent`**: Now **idempotent** - returns existing profile instead of error

### Friends  
- **`GET /friends`**: Now returns **friend profiles** with status (online/in-game/offline), not friendship records
- **`GET /friends/children/search`**: Now **excludes existing friends** and current child
- **`GET /friends/children/all`**: NEW - List all children (for discovery)

### Rooms
- **`POST /rooms`**: Now **auto-adds AI player** if no friends invited
- **`POST /rooms/join`**: Now **validates room_id** - prevents joining if already in another room
- **`POST /rooms/leave`**: If **host leaves**, entire room is **deleted**
- **`GET /rooms/current`**: Returns **`null`** (not 404) when child not in room

### Billing
- **`POST /billing/create-checkout`**: NEW - Creates Stripe checkout session

### Voice (NEW Router)
- **`POST /voice/create-voice-clone`**: NEW - Upload audio to ElevenLabs
- **`POST /voice/generate-story-audio`**: NEW - Generate TTS audio

---

## 📋 Complete Endpoint List

### Profiles (`/profiles`)
```
POST   /profiles/parent                           # Create/get parent (idempotent)
GET    /profiles/parent                           # Get parent
POST   /profiles/children                         # Create child
GET    /profiles/children                         # List children
PATCH  /profiles/children/{child_id}              # Update child
DELETE /profiles/children/{child_id}              # Delete child
POST   /profiles/children/{child_id}/status       # Update online/room status
```

### Friends (`/friends`)
```
POST   /friends/requests                          # Send friend request
POST   /friends/requests/{request_id}/accept      # Accept request
POST   /friends/requests/{request_id}/decline     # Decline request
GET    /friends?child_id={id}                     # List friends WITH STATUS ⭐
GET    /friends/requests?child_id={id}            # Get pending requests
DELETE /friends/{child_id}?friend_child_id={id}   # Unfriend
GET    /friends/children/search?q={query}&child_id={id}  # Search (excludes friends) ⭐
GET    /friends/children/all                      # List all children ⭐
```

### Rooms (`/rooms`)
#### Core
```
POST   /rooms                                     # Create room (auto-AI) ⭐
POST   /rooms/join                                # Join room (validates room_id) ⭐
POST   /rooms/leave?child_id={id}                 # Leave room (deletes if host) ⭐
POST   /rooms/close?room_id={id}                  # Close room
GET    /rooms/current?child_id={id}               # Get current room (null if none) ⭐
GET    /rooms/{room_id}/participants              # Get participants
```

#### Invitations ⭐ NEW
```
POST   /rooms/invite                              # Invite friends to room
POST   /rooms/request-to-join                     # Request to join by code
POST   /rooms/handle-join-request                 # Approve/deny join request
GET    /rooms/pending-invitations?child_id={id}   # Get pending invitations
POST   /rooms/accept-invitation?invitation_id={id}&child_id={id}
POST   /rooms/decline-invitation?invitation_id={id}&child_id={id}
```

### Sessions (`/sessions`)
```
POST   /sessions                                  # Create game session
GET    /sessions/{session_id}                     # Get session
POST   /sessions/scores                           # Save scores
GET    /sessions/{session_id}/scores              # Get session scores
GET    /sessions/room/{room_id}                   # Get all room sessions
```

### Stories (`/stories`)
```
POST   /stories                                   # Create story
GET    /stories?child_id={id}                     # List stories
GET    /stories/{story_id}                        # Get story
DELETE /stories/{story_id}                        # Delete story
```

### Billing (`/billing`)
```
POST   /billing/create-checkout                   # Create Stripe session ⭐ NEW
POST   /billing/voice-subscription                # Create/update subscription
GET    /billing/voice-subscription                # Get subscription
DELETE /billing/voice-subscription                # Cancel subscription
```

### Voice (`/voice`) ⭐ NEW ROUTER
```
POST   /voice/create-voice-clone                  # Upload audio to ElevenLabs
POST   /voice/generate-story-audio                # Generate TTS audio
```

---

## 🔄 Request/Response Examples

### Create Room (Auto-AI)
**Request:**
```json
POST /rooms
{
    "host_child_id": "uuid-here",
    "game_id": "trivia",
    "difficulty": "easy",
    "max_players": 4
    // No friend_ids - AI will be added automatically
}
```

**Response:**
```json
{
    "id": "room-uuid",
    "room_code": "ABC123",
    "host_child_id": "uuid-here",
    "current_players": 2,
    "participants": [
        {
            "id": "p1",
            "player_name": "Tommy",
            "is_ai": false
        },
        {
            "id": "p2",
            "player_name": "Alex the Explorer",
            "player_avatar": "🧭",
            "is_ai": true  // ⭐ Auto-added
        }
    ]
}
```

### List Friends with Status
**Request:**
```
GET /friends?child_id=uuid-here
```

**Response:**
```json
[
    {
        "id": "friend1-uuid",
        "name": "Alice",
        "avatar": "👧",
        "age_group": "6-8",
        "is_online": true,
        "status": "in-game"  // ⭐ Based on room_id
    },
    {
        "id": "friend2-uuid",
        "name": "Bob",
        "is_online": true,
        "status": "online"  // ⭐ Online but not in game
    },
    {
        "id": "friend3-uuid",
        "name": "Charlie",
        "is_online": false,
        "status": "offline"  // ⭐ Offline
    }
]
```

### Search Children (Excludes Friends)
**Request:**
```
GET /friends/children/search?q=Ali&child_id=current-child-uuid
```

**Response:**
```json
[
    {
        "id": "child-uuid",
        "name": "Alicia",  // ⭐ NOT already a friend
        "avatar": "👸",
        "age_group": "6-8"
    }
    // Will NOT include:
    // - Current child
    // - Existing friends
    // - Pending friend requests
]
```

### Create Stripe Checkout
**Request:**
```json
POST /billing/create-checkout
{
    "email": "parent@example.com",  // Optional
    "name": "John Doe"               // Optional
}
```

**Response:**
```json
{
    "url": "https://checkout.stripe.com/c/pay/cs_test_..."
}
```

### Create Voice Clone
**Request:**
```json
POST /voice/create-voice-clone
{
    "child_id": "uuid-here",
    "audio_data": "UklGRiQAAABXQVZFZm10...",  // base64 WAV
    "file_name": "tommy_voice.wav"
}
```

**Response:**
```json
{
    "success": true,
    "voice_id": "elevenlabs-voice-id-here",
    "data": {
        "child_id": "uuid-here",
        "voice_id": "elevenlabs-voice-id-here"
    }
}
```

---

## 🚨 Breaking Changes

### None! 
All changes are **backward compatible**:
- New behavior is **additive** or **fixes bugs**
- Existing endpoints work as before
- New optional fields in responses
- New query parameters are optional

---

## ⚙️ Configuration Required

Add to `.env`:
```bash
# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PRICE_ID=price_1SB4ZHJAv5QFU5rkK7mIII1E

# ElevenLabs
ELEVENLABS_API_KEY=your_key_here
```

Install dependencies:
```powershell
pip install stripe
```

---

## 🧪 Testing Checklist

- [ ] Parent profile creation is idempotent
- [ ] Friend search excludes existing friends
- [ ] Friend list shows correct status (online/in-game/offline)
- [ ] Room creation auto-adds AI when no friends
- [ ] Cannot join room if already in another
- [ ] Host leaving deletes entire room
- [ ] Get current room returns null (not 404)
- [ ] Stripe checkout creates session
- [ ] Voice clone requires active subscription

---

## 📚 Documentation

- **Swagger UI**: http://localhost:8080/docs
- **Migration Details**: EDGE_FUNCTION_MIGRATION.md
- **Testing Guide**: API_TESTING_GUIDE.md
