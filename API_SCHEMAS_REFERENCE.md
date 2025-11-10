# API Request/Response Schemas Reference

All API endpoints now have properly exposed request and response schemas in Swagger UI.

## Profile Endpoints

### POST /profiles/parent
**Request Body:** `ParentProfileCreate`
```json
{
  "name": "string"
}
```
**Response:** `ParentProfileResponse`

### POST /profiles/children
**Request Body:** `ChildProfileCreate`
```json
{
  "name": "string",
  "age": 0,
  "avatar": "string"
}
```
**Response:** `ChildProfileResponse`

### PATCH /profiles/children/{child_id}
**Request Body:** `ChildProfileUpdate`
```json
{
  "name": "string (optional)",
  "age": 0 (optional),
  "avatar": "string (optional)"
}
```
**Response:** `ChildProfileResponse`

### POST /profiles/children/{child_id}/status
**Request Body:** `ChildOnlineStatusUpdate`
```json
{
  "is_online": true (optional),
  "in_room": true (optional)
}
```
**Response:** `ChildProfileResponse`

## Friend Endpoints

### POST /friends/requests
**Request Body:** `FriendRequestCreate`
```json
{
  "receiver_id": "uuid"
}
```
**Response:** `FriendRequestResponse`

## Room Endpoints

### POST /rooms
**Request Body:** `GameRoomCreate`
```json
{
  "host_child_id": "uuid",
  "game_id": "string",
  "difficulty": "string",
  "max_players": 4,
  "friend_ids": ["uuid"] (optional),
  "selected_category": "string (optional)"
}
```
**Response:** `GameRoomResponse`

### POST /rooms/join
**Request Body:** `JoinRoomRequest`
```json
{
  "room_code": "string",
  "child_id": "uuid"
}
```
**Response:** `GameRoomResponse`

### POST /rooms/leave
**Request Body:** `LeaveRoomRequest`
```json
{
  "child_id": "uuid"
}
```
**Response:** 204 No Content

### POST /rooms/close
**Request Body:** `CloseRoomRequest`
```json
{
  "room_id": "uuid"
}
```
**Response:** 204 No Content

### POST /rooms/invite
**Request Body:** `InviteFriendsRequest`
```json
{
  "room_code": "string",
  "friend_ids": ["uuid"]
}
```
**Response:** `dict`

### POST /rooms/request-to-join
**Request Body:** `JoinRequestCreate`
```json
{
  "room_code": "string",
  "child_id": "uuid"
}
```
**Response:** `JoinRequestResponse`

### POST /rooms/handle-join-request
**Request Body:** `HandleJoinRequestRequest`
```json
{
  "request_id": "uuid",
  "approve": true
}
```
**Response:** `dict`

### POST /rooms/accept-invitation
**Request Body:** `AcceptInvitationRequest`
```json
{
  "invitation_id": "uuid",
  "child_id": "uuid"
}
```
**Response:** `dict`

### POST /rooms/decline-invitation
**Request Body:** `DeclineInvitationRequest`
```json
{
  "invitation_id": "uuid",
  "child_id": "uuid"
}
```
**Response:** `dict`

## Session Endpoints

### POST /sessions
**Request Body:** `GameSessionCreate`
```json
{
  "room_id": "uuid",
  "game_id": "string",
  "difficulty": "string",
  "selected_category": "string (optional)"
}
```
**Response:** `GameSessionResponse`

### POST /sessions/scores
**Request Body:** `GameScoreCreate`
```json
{
  "room_id": "uuid",
  "session_id": "uuid",
  "child_id": "uuid (optional)",
  "score": 0,
  "time_spent": 0 (optional),
  "questions_answered": 0 (optional),
  "correct_answers": 0 (optional)
}
```
**Response:** `GameScoreResponse`

## Story Endpoints

### POST /stories
**Request Body:** `GeneratedStoryCreate`
```json
{
  "child_id": "uuid",
  "prompt": "string",
  "story_text": "string",
  "image_url": "string (optional)",
  "audio_url": "string (optional)"
}
```
**Response:** `GeneratedStoryResponse`

## Billing Endpoints

### POST /billing/create-checkout
**Request Body:** `CheckoutRequest`
```json
{
  "email": "string (optional)",
  "name": "string (optional)"
}
```
**Response:** `CheckoutResponse`

### POST /billing/voice-subscription
**Request Body:** (Auto-generated from query params)
```json
{
  "parent_id": "uuid",
  "stripe_customer_id": "string",
  "stripe_subscription_id": "string"
}
```
**Response:** `VoiceSubscriptionResponse`

## Voice Endpoints

### POST /voice/create-voice-clone
**Request Body:** `VoiceCloneRequest`
```json
{
  "child_id": "string",
  "audio_data": "string (base64)",
  "file_name": "string (optional)"
}
```
**Response:** `VoiceCloneResponse`

### POST /voice/generate-story-audio
**Request Body:** `StoryAudioRequest`
```json
{
  "story_text": "string",
  "voice_id": "string"
}
```
**Response:** `StoryAudioResponse`

## Changes Made

### New Schema Models Added:
1. **LeaveRoomRequest** - For `/rooms/leave` endpoint
2. **CloseRoomRequest** - For `/rooms/close` endpoint
3. **AcceptInvitationRequest** - For `/rooms/accept-invitation` endpoint
4. **DeclineInvitationRequest** - For `/rooms/decline-invitation` endpoint

### Endpoints Updated:
- **POST /rooms/leave** - Changed from query parameters to request body
- **POST /rooms/close** - Changed from query parameters to request body
- **POST /rooms/accept-invitation** - Changed from query parameters to request body
- **POST /rooms/decline-invitation** - Changed from query parameters to request body

### Schema Exports Updated:
- Added new schemas to `app/schemas/__init__.py` exports
- Added `GameScoreCreate` and `GameScoreResponse` to exports
- All schemas now properly imported in router files

## Testing in Swagger UI

1. Start the server: `python -m uvicorn app.main:app --reload --port 8080`
2. Open Swagger UI: http://localhost:8080/docs
3. All POST/PUT/PATCH endpoints now show:
   - **Request body** section with schema and example
   - **Response** section with schema and example
   - Interactive "Try it out" functionality with pre-filled examples

## Benefits

✅ **Better API Documentation** - All request bodies are clearly documented in Swagger UI
✅ **Improved Developer Experience** - Developers can see exactly what data to send
✅ **Type Safety** - Pydantic validates all request bodies against schemas
✅ **Consistent API Design** - All endpoints use request bodies instead of mixing query params
✅ **Auto-generated Examples** - Swagger UI shows example JSON for each endpoint
