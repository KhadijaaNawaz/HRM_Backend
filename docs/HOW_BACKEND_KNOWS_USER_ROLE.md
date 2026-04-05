# How Backend Knows User Role at Login Time

## The Flow: Discovery During Login

The backend doesn't pre-know anything about the user. It discovers everything **during** the login process.

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. Login Request Arrives                     │
│                                                                 │
│  POST http://127.0.0.1:8000/api/v1/auth/login/                 │
│  Headers:                                                      │
│    Host: acme.localhost           ← Tells: WHICH tenant        │
│    Body: { email, password }      ← Tells: WHO is logging in   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              2. TenantMiddleware (First Step)                   │
│                                                                 │
│  Read Host header: "acme.localhost"                             │
│         │                                                       │
│         ▼                                                       │
│  Query domains table (public schema):                          │
│    SELECT * FROM domains WHERE domain = 'acme.localhost';       │
│         │                                                       │
│         ▼                                                       │
│  Get: tenant_id = "acme-org-uuid"                             │
│         │                                                       │
│         ▼                                                       │
│  SWITCH to tenant schema: SET search_path = 'acme'             │
│         │                                                       │
│         ▼                                                       │
│  All subsequent queries now use "acme" schema automatically    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  3. LoginView (In acme schema)                  │
│                                                                 │
│  Now in "acme" schema, query for user:                         │
│    SELECT * FROM users WHERE email = 'admin@acme.com';          │
│         │                                                       │
│         └──> This queries acme.users table!                     │
│              (Not public.users)                                  │
│         │                                                       │
│         ▼                                                       │
│  Found user! Now read their attributes:                         │
│    - id: "user-uuid"                                           │
│    - email: "admin@acme.com"                                   │
│    - password: "hashed_password"                               │
│    - is_superuser: false          ← BOOLEAN FIELD IN DB         │
│    - is_tenant_admin: true          ← BOOLEAN FIELD IN DB       │
│    - is_active: true                                          │
│         │                                                       │
│         ▼                                                       │
│  Verify password using Django's check_password()               │
│         │                                                       │
│         ▼                                                       │
│  Generate JWT tokens with user info                            │
│         │                                                       │
│         ▼                                                       │
│  Return response with user data:                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    4. Response to Frontend                      │
│                                                                 │
│  {                                                              │
│    "access": "jwt_token...",                                   │
│    "user": {                                                   │
│      "email": "admin@acme.com",                                │
│      "is_superuser": false,        ← Read from DB              │
│      "is_tenant_admin": true,        ← Read from DB             │
│      "roles": [                   ← Read from DB via UserRole    │
│        { "name": "Admin" }                                      │
│      ]                                                           │
│    }                                                             │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema for Each Tenant

```
acme schema (tenant)
│
└── users table
    ├── id: uuid (PK)
    ├── email: varchar (unique)
    ├── password_hash: varchar
    ├── is_superuser: boolean     ← THIS IS HOW IT KNOWS!
    ├── is_tenant_admin: boolean   ← THIS TOO!
    ├── is_active: boolean
    └── other fields...
```

---

## Code-Level Flow

### Backend: LoginView (accounts/views.py)

```python
class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        # Step 1: Validate email/password
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Step 2: Get user (from CURRENT schema set by middleware)
        user = serializer.validated_data['user']
        # ↑ This user is already fetched from acme.users table
        #   because TenantMiddleware switched the schema

        # Step 3: Check user's attributes from database
        print(f"User: {user.email}")
        print(f"Is Superuser: {user.is_superuser}")      # ← Direct DB field
        print(f"Is Tenant Admin: {user.is_tenant_admin}") # ← Direct DB field
        print(f"Roles: {list(user.roles.all())}")        # ← Query via UserRole

        # Step 4: Generate JWT with user info
        refresh = RefreshToken.for_user(user)

        # Step 5: Return user data (backend NOW knows!)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': MeSerializer(user).data
        })
```

### Backend: User Model (accounts/models.py)

```python
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_superuser = models.BooleanField(default=False)   # ← Stored in DB
    is_tenant_admin = models.BooleanField(default=False) # ← Stored in DB

    @property
    def roles(self):
        # Query UserRole table to get user's roles
        return Role.objects.filter(role_users__user=self)
```

---

## Timeline: When Does Backend Know What?

```
Time  ──────────────────────────────────────────────────────────>
       │
       │  Request arrives
       ▼
┌──────────────┐
│ Backend has  │
│ NO IDEA yet  │
│ who user is  │
└──────┬───────┘
       │
       │ Read Host header
       ▼
┌──────────────┐
│ Backend knows│
│ tenant = acme │
│ (but not who) │
└──────┬───────┘
       │
       │ Query DB in acme schema
       ▼
┌──────────────┐
│ Backend finds│
│ user in DB   │
└──────┬───────┘
       │
       │ Read user fields
       ▼
┌──────────────┐
│ Backend NOW  │
│ KNOWS:       │
│ - email      │
│ - is_superuser     ← Read from DB field
│ - is_tenant_admin ← Read from DB field
│ - roles            ← Read from UserRole table
└──────────────┘
```

---

## The Key Insight

### BEFORE Login Request
- Backend knows: **NOTHING** about the user
- Backend only knows: **Which tenant** (from Host header)

### DURING Login Request
- Backend queries the database
- Backend reads the user's fields
- Backend **discovers** the user's role

### AFTER Login Request
- Backend returns the role info in the response
- Frontend now knows the user's role
- Frontend can show/hide UI accordingly

---

## Example: Different Users, Same Process

### User 1: Superuser Logs In

```python
# Request: POST /api/v1/auth/login/
# Host: acme.localhost
# Body: { email: "superadmin@hrmsaas.com", password: "..." }

# Backend process:
1. TenantMiddleware: Host=acme.localhost → schema=acme
2. LoginView: SELECT * FROM acme.users WHERE email='superadmin@hrmsaas.com'
3. User found:
   - is_superuser = true   ← Read from DB
   - is_tenant_admin = true ← Read from DB
4. Return: { user: { is_superuser: true, ... } }
```

### User 2: Regular Employee Logs In

```python
# Request: POST /api/v1/auth/login/
# Host: acme.localhost
# Body: { email: "employee@acme.com", password: "..." }

# Backend process:
1. TenantMiddleware: Host=acme.localhost → schema=acme
2. LoginView: SELECT * FROM acme.users WHERE email='employee@acme.com'
3. User found:
   - is_superuser = false  ← Read from DB
   - is_tenant_admin = false ← Read from DB
   - roles = [Employee] ← Query from UserRole table
4. Return: { user: { is_superuser: false, is_tenant_admin: false, roles: [...] } }
```

---

## Database Query Example

```sql
-- When user logs in, backend runs this (in acme schema):

SELECT id, email, password, is_superuser, is_tenant_admin, is_active
FROM users
WHERE email = 'admin@acme.com';

-- Result:
-- id | email              | is_superuser | is_tenant_admin | is_active
----+--------------------+--------------+-----------------+------------
-- uuid... | admin@acme.com   | false        | true            | true

-- Then queries roles:
SELECT r.name, r.description
FROM roles r
JOIN user_roles ur ON ur.role_id = r.id
WHERE ur.user_id = 'uuid...';

-- Result:
-- name   | description
----+---------------------------
-- Admin | Tenant administrator...
```

---

## Frontend: Using the Response

```typescript
// Frontend receives the response
const loginResponse = await fetch('/api/v1/auth/login/', {
  method: 'POST',
  headers: { 'Host': 'acme.localhost' },
  body: JSON.stringify({ email, password })
});

const data = await loginResponse.json();

// Backend has NOW told frontend what role this user has
console.log('Is Superuser?', data.user.is_superuser);
console.log('Is Tenant Admin?', data.user.is_tenant_admin);
console.log('Roles?', data.user.roles);

// Store and use for UI
localStorage.setItem('user', JSON.stringify(data.user));

// Show/hide features based on what backend told us
if (data.user.is_superuser) {
  // Show admin panel
}
if (data.user.is_tenant_admin) {
  // Show user management, roles, etc.
}
if (data.user.roles.some(r => r.name === 'HR')) {
  // Show HR features
}
```

---

## Summary

| Question | Answer |
|----------|--------|
| **Does backend know before login?** | No, only knows which tenant from Host header |
| **When does backend know user role?** | After querying database during login |
| **Where is role stored?** | In `is_superuser`, `is_tenant_admin` fields and `roles` table in user's tenant schema |
| **How does backend find it?** | SQL query: `SELECT is_superuser, is_tenant_admin FROM users WHERE email = ?` |
| **What's returned to frontend?** | User object with all flags and roles |

**The key point:** The backend "discovers" user role by **reading from database** during the login process. It's not pre-known or assumed - it's queried from the user's record in the tenant's schema.
