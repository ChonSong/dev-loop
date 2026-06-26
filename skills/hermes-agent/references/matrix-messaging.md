# Hermes Container — External API Access Patterns

## Matrix Messaging from Container

**Server:** Synapse at `http://192.168.1.103:8008`  
**Client (Cinny):** `http://192.168.1.103:8080`  
**Homeserver domain:** `hermes.local`

### Register a New User

Step 1 returns a session ID, step 2 completes with `m.login.dummy` auth type.  
If `M_USER_IN_USE`: user already exists (possibly deactivated), go to login.  
If `M_USER_DEACTIVATED`: pick a fresh username.

### Login (Existing User)

Use `identifier: {type: "m.id.user", user: "..."}` — the bare `user` field returns `M_INVALID_USERNAME`.

### Send a Message

Use `subprocess` list args with Python f-strings for the token — **never** shell variable interpolation.  
Token truncation causes cryptic `M_UNKNOWN_TOKEN` errors.

### Known Room

- `#agent-messaging:hermes.local` — Room ID: `!gICWwOAv3bvdBe9Tc71vBne5uK-hb7HRUlznAu7gJgM`
- Members: `@hermes:hermes.local` (admin), `@hermes2:hermes.local` (auto-responder), `@zoul:hermes.local`

Full code examples: see the session transcript or ask OWL to reconstruct.
