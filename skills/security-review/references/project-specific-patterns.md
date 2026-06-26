# Project-Specific Security Patterns

## agent-os (Node/Express) and hermes-web-computer (Go)

### Secrets Management

**NEVER:**
```typescript
const apiKey = "sk-***"  // Hardcoded
const dbPassword = "pass123"
```

**ALWAYS:**
```typescript
// Node/Express
const apiKey = process.env.OPENAI_API_KEY
if (!apiKey) throw new Error('OPENAI_API_KEY not configured')

// Go
apiKey := os.Getenv("OPENAI_API_KEY")
if apiKey == "" {
    log.Fatal("OPENAI_API_KEY not configured")
}
```

**Checklist:**
- [ ] No hardcoded keys, tokens, passwords
- [ ] All secrets in environment variables
- [ ] `.env.local` in `.gitignore`
- [ ] No secrets in git history

### Input Validation

**Node/Express (Zod):**
```typescript
import { z } from 'zod'

const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
})

export async function createUser(input: unknown) {
  const validated = CreateUserSchema.parse(input)
  return await db.users.create(validated)
}
```

**Go (standard library):**
```go
type CreateUserInput struct {
    Email string `json:"email"`
    Name  string `json:"name"`
}

func validateCreateInput(input CreateUserInput) error {
    if input.Email == "" || !isValidEmail(input.Email) {
        return errors.New("invalid email")
    }
    if len(input.Name) < 1 || len(input.Name) > 100 {
        return errors.New("invalid name")
    }
    return nil
}
```

**File Upload Validation:**
- Size check (5MB max default)
- Type whitelist (not blacklist)
- Extension check
- Never trust `Content-Type` header

### SQL Injection Prevention

**NEVER:**
```typescript
const query = `SELECT * FROM users WHERE email = '${userEmail}'`
```

**ALWAYS:**
```typescript
// Supabase/Prisma - parameterized
const { data } = await supabase
  .from('users')
  .select('*')
  .eq('email', userEmail)

// Go - parameterized
rows, err := db.Query("SELECT * FROM users WHERE email = $1", userEmail)
```

### XSS Prevention

**Node:**
```typescript
import DOMPurify from 'isomorphic-dompurify'
const safe = DOMPurify.sanitize(userInput)
```

**Svelte (auto-escaped):**
```svelte
<!-- SAFE: auto-escaped -->
<p>{userInput}</p>

<!-- DANGEROUS: disables escaping -->
{@html userInput}  <!-- Only with sanitized input -->
```

**React:**
```jsx
// SAFE: JSX auto-escapes
<p>{userInput}</p>

<!-- DANGEROUS: disables escaping -->
<div dangerouslySetInnerHTML={{__html: userInput}} />
```

### Authentication

**Token Storage:**
- **FAIL:** `localStorage.setItem('token', token)` — vulnerable to XSS
- **PASS:** httpOnly cookies — `Set-Cookie: token=xxx; HttpOnly; Secure; SameSite=Strict`

**Authorization Checks:**
```typescript
// ALWAYS verify authorization FIRST
if (requester.role !== 'admin') {
    return res.status(403).json({ error: 'Unauthorized' })
}
// Proceed with operation
```

### Rate Limiting

**Express:**
```typescript
import rateLimit from 'express-rate-limit'

const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100,
    message: 'Too many requests'
})
app.use('/api/', limiter)
```

### Pre-Commit Security Checklist (agent-os / HWC)

- [ ] No hardcoded secrets
- [ ] All user inputs validated
- [ ] SQL queries parameterized
- [ ] XSS prevention in place
- [ ] Auth checks before sensitive ops
- [ ] Rate limiting on public endpoints
- [ ] Error messages don't leak sensitive data
- [ ] CORS configured correctly
- [ ] HTTPS enforced in production
