# HRM SaaS Frontend - Complete UI Generation Prompt

## Executive Summary

You are tasked with creating a complete, production-ready frontend for a multi-tenant HRM SaaS application. This is a comprehensive project that requires implementing all pages, components, authentication, state management, and API integrations specified in this document.

## Technology Stack (Strictly Follow This)

### Core Framework
- **React 18+** with **TypeScript** (strict mode enabled)
- **Vite** as the build tool (create with: `npm create vite@latest hrm-saas-frontend -- --template react-ts`)

### State Management & Data Fetching
- **@tanstack/react-query** (latest version) for server state management and caching
- **Zustand** for global client state (authentication, UI state)

### Routing & Navigation
- **React Router v6** with lazy loading for code splitting

### HTTP Client
- **Axios** for API calls with custom interceptors

### Forms & Validation
- **React Hook Form** for form management
- **Zod** for schema validation
- **@hookform/resolvers** for connecting Zod with React Hook Form

### UI/Styling
- **TailwindCSS v3** for styling
- **@headlessui/react** for accessible UI components (modals, dropdowns, tabs)
- **@heroicons/react** for consistent iconography
- **clsx** and **tailwind-merge** for conditional class management

### Date/Time Handling
- **date-fns** for all date formatting and manipulation

### Installation Commands
```bash
npm create vite@latest hrm-saas-frontend -- --template react-ts
cd hrm-saas-frontend
npm install @tanstack/react-query@latest
npm install axios react-router-dom zustand
npm install react-hook-form @hookform/resolvers zod
npm install date-fns clsx tailwind-merge
npm install @headlessui/react @heroicons/react
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

---

## Project Architecture & Structure

### Folder Structure (Strictly Follow This)
```
src/
├── components/
│   ├── auth/
│   │   ├── LoginForm.tsx              # Login page form
│   │   ├── ForgotPasswordForm.tsx     # Forgot password form
│   │   ├── ResetPasswordForm.tsx      # Password reset form
│   │   ├── AcceptInviteForm.tsx       # Accept invitation form
│   │   └── index.ts
│   ├── users/
│   │   ├── UserList.tsx               # Table of all users (Admin/HR)
│   │   ├── UserForm.tsx               # Create/Edit user form
│   │   ├── UserCard.tsx               # User display card
│   │   ├── UserDetail.tsx             # Single user detail view
│   │   ├── UserRoleManager.tsx        # Assign/revoke roles
│   │   └── index.ts
│   ├── attendance/
│   │   ├── AttendanceActions.tsx      # Check-in/Check-out widget
│   │   ├── AttendanceList.tsx         # Attendance records table
│   │   ├── AttendanceReport.tsx       # Monthly attendance report
│   │   ├── AttendanceCalendar.tsx     # Calendar view of attendance
│   │   └── index.ts
│   ├── invitations/
│   │   ├── InvitationForm.tsx         # Send invitation form
│   │   ├── InvitationList.tsx         # List of pending invitations
│   │   └── index.ts
│   ├── roles/
│   │   ├── RoleList.tsx               # List of all roles
│   │   ├── RoleForm.tsx               # Create/edit role
│   │   └── index.ts
│   ├── organization/
│   │   ├── OrganizationOverview.tsx   # Dashboard stats
│   │   ├── OrganizationSettings.tsx   # Org settings form
│   │   └── index.ts
│   ├── admin/
│   │   ├── TenantList.tsx             # List all tenants (superuser)
│   │   ├── TenantForm.tsx             # Create tenant form
│   │   ├── TenantDetail.tsx           # Tenant details
│   │   └── index.ts
│   ├── layout/
│   │   ├── Header.tsx                 # Top navigation bar
│   │   ├── Sidebar.tsx                # Side navigation
│   │   ├── Layout.tsx                 # Main layout wrapper
│   │   ├── MobileNav.tsx              # Mobile navigation
│   │   └── index.ts
│   ├── common/
│   │   ├── Button.tsx                 # Reusable button
│   │   ├── Input.tsx                  # Reusable input
│   │   ├── Select.tsx                 # Reusable select
│   │   ├── Modal.tsx                  # Modal dialog
│   │   ├── Table.tsx                  # Reusable table
│   │   ├── Pagination.tsx             # Pagination component
│   │   ├── ConfirmDialog.tsx          # Confirmation dialog
│   │   ├── LoadingSpinner.tsx         # Loading indicator
│   │   ├── ErrorMessage.tsx           # Error display
│   │   ├── EmptyState.tsx             # Empty state display
│   │   └── index.ts
│   ├── ProtectedRoute.tsx             # Auth wrapper
│   ├── ErrorBoundary.tsx              # Error boundary
│   └── index.ts
├── pages/
│   ├── LoginPage.tsx                  # /login
│   ├── ForgotPasswordPage.tsx         # /forgot-password
│   ├── ResetPasswordPage.tsx          # /reset-password
│   ├── AcceptInvitePage.tsx           # /accept-invite
│   ├── DashboardPage.tsx              # /dashboard
│   ├── UsersPage.tsx                  # /users
│   ├── UserDetailPage.tsx             # /users/:id
│   ├── AttendancePage.tsx             # /attendance
│   ├── AttendanceReportPage.tsx       # /attendance/report
│   ├── InvitationsPage.tsx            # /invitations
│   ├── RolesPage.tsx                  # /roles
│   ├── OrganizationPage.tsx           # /organization
│   ├── SettingsPage.tsx               # /settings
│   ├── ProfilePage.tsx                # /profile
│   ├── AdminTenantsPage.tsx           # /admin/tenants
│   ├── UnauthorizedPage.tsx           # /unauthorized
│   ├── NotFoundPage.tsx               # /404
│   └── index.ts
├── stores/
│   ├── auth-store.ts                  # Authentication state
│   ├── ui-store.ts                    # UI state (modals, sidebar)
│   └── index.ts
├── lib/
│   ├── api-client.ts                  # Axios instance with interceptors
│   ├── api.ts                         # API service functions
│   ├── react-query.ts                 # React Query client
│   ├── utils.ts                       # Utility functions (cn, format, etc.)
│   └── validations.ts                 # Zod schemas
├── hooks/
│   ├── useApiError.ts                 # API error handling
│   ├── useAuth.ts                     # Auth helpers
│   ├── usePermission.ts               # Permission checking
│   ├── useDebounce.ts                 # Debounce hook
│   └── index.ts
├── types/
│   ├── api.types.ts                   # API response types
│   ├── models.types.ts                # Domain model types
│   └── index.ts
├── constants/
│   ├── routes.ts                      # Route definitions
│   ├── permissions.ts                 # Permission constants
│   ├── roles.ts                       # Role definitions
│   └── index.ts
├── App.tsx                            # Root app component
├── main.tsx                           # Entry point
└── vite-env.d.ts
```

---

## Complete Page Specifications

### 1. Authentication Pages

#### 1.1 Login Page (`/login`)
**Requirements:**
- Clean, centered card layout
- Email and password fields with proper validation
- "Forgot Password?" link
- Error message display
- Loading state during authentication
- Remember me checkbox
- Redirect to dashboard on success
- Handle subdomain-based tenant detection

**Fields:**
- Email (required, email format)
- Password (required, min 8 chars)
- Remember Me (checkbox)

**API Endpoints:**
- POST `/api/v1/auth/login/`

---

#### 1.2 Forgot Password Page (`/forgot-password`)
**Requirements:**
- Simple form with email field
- Instructions text
- Success message after submission
- Link back to login

**Fields:**
- Email (required, email format)

**API Endpoints:**
- POST `/api/v1/auth/password/forgot/`

---

#### 1.3 Reset Password Page (`/reset-password`)
**Requirements:**
- Accessible via token in URL
- New password and confirm password fields
- Password strength indicator
- Error handling for invalid/expired tokens

**Fields:**
- New Password (required, min 8 chars)
- Confirm Password (required, must match)

**API Endpoints:**
- POST `/api/v1/auth/password/reset/`

---

#### 1.4 Accept Invitation Page (`/accept-invite`)
**Requirements:**
- Accessible via invitation token
- Show invitation details (email, role)
- Fields: password, first name, last name
- Auto-login after acceptance

**Fields:**
- First Name (required)
- Last Name (required)
- Password (required, min 8 chars)
- Confirm Password (required, must match)

**API Endpoints:**
- POST `/api/v1/invite/accept/`

---

### 2. Dashboard Pages

#### 2.1 Main Dashboard (`/dashboard`)
**Requirements:**
- Welcome message with user name
- Quick action cards (Check In/Out, View Attendance, Invite User)
- Statistics cards (Total Employees, Present Today, Absent Today, Late Today)
- Recent activity feed
- Quick access to common tasks
- Role-based content (Employee vs HR/Admin vs Superuser)

**Widgets:**
1. **Attendance Widget** - Check-in/check-out button with current time display
2. **Stats Cards** - 4 cards with icons and numbers
3. **Recent Activity** - List of recent actions in the tenant
4. **Upcoming Birthdays/Anniversaries** - (optional enhancement)

**API Endpoints:**
- GET `/api/v1/organization/overview/`
- GET `/api/v1/attendance/` (today's records)
- GET `/api/v1/users/me/`

---

### 3. User Management Pages

#### 3.1 Users List Page (`/users`)
**Access Control:** Admin, HR only

**Requirements:**
- Data table with pagination (20 per page)
- Search by name or email
- Filter by role and status (active/inactive)
- Sort by any column
- Actions per row: View, Edit, Delete, Manage Roles
- Bulk actions: Activate, Deactivate, Delete
- "Add New User" button (opens modal/form)
- Export to CSV functionality

**Table Columns:**
- Avatar (initials or image)
- Full Name
- Email
- Phone
- Roles (badges)
- Status (Active/Inactive badge)
- Join Date
- Actions (dropdown menu)

**API Endpoints:**
- GET `/api/v1/users/` (list with filters)
- DELETE `/api/v1/users/{id}/`
- PATCH `/api/v1/users/{id}/`

---

#### 3.2 User Detail Page (`/users/:id`)
**Access Control:** Admin, HR, or own profile

**Requirements:**
- User profile header with avatar, name, email
- Tabs: Overview, Attendance, Roles, Activity
- Overview tab: Personal info, contact info, employment details
- Attendance tab: Attendance history with calendar view
- Roles tab: Current roles, assign new role, remove role
- Activity tab: Recent actions/audit logs
- Edit button (Admin/HR only)
- Deactivate button (Admin/HR only)

**API Endpoints:**
- GET `/api/v1/users/{id}/`
- GET `/api/v1/attendance/?user_id={id}`
- GET `/api/v1/roles/`

---

#### 3.3 Create/Edit User Modal
**Requirements:**
- Form with validation
- Password required for create, optional for edit
- Role assignment (multi-select)
- Phone number (optional)
- Profile picture upload (optional)

**Fields:**
- First Name (required)
- Last Name (required)
- Email (required, unique)
- Phone (optional)
- Password (required for create)
- Confirm Password (required for create)
- Roles (multi-select, at least one)

**API Endpoints:**
- POST `/api/v1/users/` (create)
- PATCH `/api/v1/users/{id}/` (update)

---

### 4. Attendance Pages

#### 4.1 Attendance Page (`/attendance`)
**Access Control:** All authenticated users

**For Employees:**
- Personal attendance view only
- Check-in/check-out widget prominent
- Today's status card
- Current month calendar with attendance indicators
- Weekly summary

**For HR/Admin:**
- All employees' attendance
- Filter by user, date range, status
- Export functionality
- Team attendance summary
- Attendance exceptions/reviews

**Table Columns (Admin/HR view):**
- Employee (avatar, name)
- Date
- Check-in time
- Check-out time
- Work hours
- Status (Present, Absent, Late, Half Day)
- Notes
- Actions (Edit, View Details)

**API Endpoints:**
- GET `/api/v1/attendance/` (list with filters)
- POST `/api/v1/attendance/check-in/`
- POST `/api/v1/attendance/check-out/`
- GET `/api/v1/attendance/settings/`

---

#### 4.2 Attendance Report Page (`/attendance/report`)
**Access Control:** Admin, HR

**Requirements:**
- Month and year selector
- Summary cards: Total days, Present, Absent, Late, Half Days
- Employee-wise breakdown table
- Department-wise breakdown (if departments exist)
- Visual charts: Bar chart for monthly trends, pie chart for status distribution
- Export to PDF/CSV
- Print-friendly layout

**API Endpoints:**
- GET `/api/v1/attendance/report/`

---

#### 4.3 Check In/Out Widget Component
**Requirements:**
- Prominent display on dashboard and attendance page
- Large, easy-to-tap button
- Current date/time display
- User's current status (Not checked in, Checked in, Checked out)
- Notes field (optional, for check-in/check-out)
- Geolocation capture (optional, with user permission)
- Animation for state changes
- Toast notification on success

**API Endpoints:**
- POST `/api/v1/attendance/check-in/`
- POST `/api/v1/attendance/check-out/`

---

### 5. Invitation Pages

#### 5.1 Invitations Page (`/invitations`)
**Access Control:** Admin, HR

**Requirements:**
- List of all invitations (pending, accepted, expired, cancelled)
- Filter by status
- "Send New Invitation" button
- Actions per invitation: Resend, Cancel, View
- Show invitation details: email, role, sent date, expiry date, status
- Sort by sent date

**Table Columns:**
- Email
- Role
- Status (badge: Pending, Accepted, Expired, Cancelled)
- Sent Date
- Expires Date
- Sent By
- Actions

**API Endpoints:**
- GET `/api/v1/invite/` (list)
- POST `/api/v1/invite/` (create)
- DELETE `/api/v1/invite/{id}/` (cancel)
- POST `/api/v1/invite/resend/` (resend)

---

#### 5.2 Send Invitation Modal
**Requirements:**
- Email input (required)
- Role selection (dropdown)
- Personal message (optional)
- Preview of email content
- Send button with loading state
- Success message with confirmation

**Fields:**
- Email Address (required, email format)
- Role (required, select from available roles)
- Personal Message (optional, textarea)

**API Endpoints:**
- POST `/api/v1/invite/`

---

### 6. Role Management Pages

#### 6.1 Roles Page (`/roles`)
**Access Control:** Admin only

**Requirements:**
- List of all roles (system and custom)
- Distinguish system roles (Admin, HR, Employee) - non-deletable
- "Create New Role" button
- Actions: View, Edit, Delete (custom roles only)
- Show user count per role
- Permissions overview per role

**Table Columns:**
- Role Name
- Description
- Type (System/Custom badge)
- Users Count
- Actions

**API Endpoints:**
- GET `/api/v1/roles/` (list)
- POST `/api/v1/roles/` (create)
- PATCH `/api/v1/roles/{id}/` (update)
- DELETE `/api/v1/roles/{id}/` (delete)

---

#### 6.2 Role Detail/Modal
**Requirements:**
- Role name and description
- List of users with this role
- Assign/Remove users
- For custom roles: Edit name and description

**API Endpoints:**
- GET `/api/v1/roles/{id}/`
- POST `/api/v1/roles/{id}/assign/`
- POST `/api/v1/roles/{id}/revoke/`

---

### 7. Organization Pages

#### 7.1 Organization Overview (`/organization`)
**Access Control:** Admin, HR

**Requirements:**
- Organization name and logo display
- Statistics cards: Total employees, departments, active invitations
- Recent activity timeline
- Quick actions: Add user, Send invitation, View reports
- Organization settings link

**API Endpoints:**
- GET `/api/v1/organization/overview/`

---

#### 7.2 Organization Settings (`/organization/settings`)
**Access Control:** Admin only

**Requirements:**
- Form with organization settings
- Sections: General, Attendance, Notifications

**General Settings:**
- Organization Name (required)
- Timezone (select dropdown with all timezones)
- Work Days (checkboxes for Mon-Sun)
- Required working days per month (number input)

**Attendance Settings:**
- Check-in required time (time input)
- Check-out time (time input)
- Grace period for late arrival (number input, minutes)
- Require location for check-in/out (toggle)
- IP restriction (toggle) - (future enhancement)

**Notification Settings:**
- Email notifications for attendance (toggle)
- Email notifications for invitations (toggle)

**API Endpoints:**
- GET `/api/v1/organization/settings/`
- PATCH `/api/v1/organization/settings/`

---

### 8. Settings & Profile Pages

#### 8.1 Profile Page (`/profile`)
**Access Control:** All authenticated users (own profile)

**Requirements:**
- Profile header with avatar, name, email
- Tabs: Personal Information, Security, Preferences

**Personal Information Tab:**
- Editable form: First name, Last name, Phone
- Email display (read-only, contact admin to change)
- Avatar upload

**Security Tab:**
- Current password, new password, confirm password
- Change password button

**Preferences Tab:**
- Theme selection (Light/Dark) - (future)
- Language selection (future)
- Notification preferences

**API Endpoints:**
- GET `/api/v1/users/me/`
- PATCH `/api/v1/users/me/`
- POST `/api/v1/auth/password/change/`

---

### 9. Admin Pages (Superuser Only)

#### 9.1 Tenants Management (`/admin/tenants`)
**Access Control:** Superuser only

**Requirements:**
- List of all tenants
- Filter by status (Active, Suspended)
- Search by name or domain
- "Create New Tenant" button
- Actions per tenant: View, Edit, Activate, Suspend, Delete
- Show tenant stats: user count, status, created date

**Table Columns:**
- Organization Name
- Domain/Subdomain
- Schema Name
- Status (Active/Suspended badge)
- Users Count
- Created Date
- Actions

**API Endpoints:**
- GET `/api/v1/admin/tenants/`
- POST `/api/v1/admin/create-tenant/`
- PATCH `/api/v1/admin/tenants/{id}/`
- DELETE `/api/v1/admin/tenants/{id}/`

---

#### 9.2 Create Tenant Modal
**Requirements:**
- Multi-step form or well-organized single form

**Fields:**
- Organization Information:
  - Organization Name (required)
  - Slug/Domain (required, unique, auto-generated from name)
  - Admin Email (required, unique)
  - Admin Password (required)
  - Admin First Name (required)
  - Admin Last Name (required)

**API Endpoints:**
- POST `/api/v1/admin/create-tenant/`

---

### 10. Common/Error Pages

#### 10.1 Unauthorized Page (`/unauthorized`)
**Requirements:**
- Clear message: "You don't have permission to access this page"
- Explanation of permissions
- Link to dashboard
- Contact admin for access
- Friendly illustration/icon

---

#### 10.2 Not Found Page (`/404`)
**Requirements:**
- "Page not found" message
- Link to dashboard
- Search functionality (optional)
- Friendly illustration

---

## API Integration Specifications

### API Client Configuration

**Base URL:** From environment variable `VITE_API_BASE_URL` (default: `http://127.0.0.1:8000`)

**Critical Requirements:**
1. **Subdomain Support**: The `Host` header must be set correctly for tenant resolution
   - Extract subdomain from current URL (e.g., `acme.localhost:3000` → `acme.localhost`)
   - For development: Support `.localhost` subdomains
   - For production: Use actual hostname

2. **Token Management**:
   - Store access token and refresh token in localStorage (or secure cookie for production)
   - Include access token in `Authorization: Bearer {token}` header
   - Implement automatic token refresh on 401 responses
   - Clear tokens on logout

3. **Request Interceptor**:
   - Add `Host` header for tenant resolution
   - Add `Authorization` header if token exists
   - Add request ID for tracking

4. **Response Interceptor**:
   - Handle 401 errors with token refresh
   - Redirect to login on refresh failure
   - Handle other error status codes globally
   - Extract and format error messages

**Complete API Service Functions to Implement:**

```typescript
// Authentication APIs
authApi.login(data: LoginRequest): Promise<LoginResponse>
authApi.logout(refreshToken: string): Promise<void>
authApi.getCurrentUser(): Promise<User>
authApi.refreshToken(refreshToken: string): Promise<TokenResponse>
authApi.changePassword(data: ChangePasswordRequest): Promise<void>
authApi.forgotPassword(data: ForgotPasswordRequest): Promise<void>
authApi.resetPassword(data: ResetPasswordRequest): Promise<void>

// User APIs
userApi.list(params?: ListParams): Promise<PaginatedResponse<User>>
userApi.get(id: string): Promise<User>
userApi.create(data: CreateUserRequest): Promise<User>
userApi.update(id: string, data: UpdateUserRequest): Promise<User>
userApi.delete(id: string): Promise<void>
userApi.getMe(): Promise<User>
userApi.updateMe(data: UpdateUserRequest): Promise<User>

// Role APIs
roleApi.list(): Promise<Role[]>
roleApi.get(id: string): Promise<Role>
roleApi.create(data: CreateRoleRequest): Promise<Role>
roleApi.update(id: string, data: UpdateRoleRequest): Promise<Role>
roleApi.delete(id: string): Promise<void>
roleApi.assign(roleId: string, userId: string): Promise<void>
roleApi.revoke(roleId: string, userId: string): Promise<void>

// Invitation APIs
invitationApi.list(params?: InvitationListParams): Promise<PaginatedResponse<Invitation>>
invitationApi.create(data: CreateInvitationRequest): Promise<Invitation>
invitationApi.accept(data: AcceptInvitationRequest): Promise<void>
invitationApi.cancel(id: string): Promise<void>
invitationApi.resend(email: string): Promise<void>

// Attendance APIs
attendanceApi.list(params?: AttendanceListParams): Promise<PaginatedResponse<AttendanceRecord>>
attendanceApi.checkIn(data?: CheckInRequest): Promise<AttendanceRecord>
attendanceApi.checkOut(data?: CheckOutRequest): Promise<AttendanceRecord>
attendanceApi.getReport(params?: ReportParams): Promise<AttendanceReport>
attendanceApi.getSettings(): Promise<AttendanceSettings>

// Organization APIs
organizationApi.getOverview(): Promise<OrganizationOverview>
organizationApi.getSettings(): Promise<OrganizationSettings>
organizationApi.updateSettings(data: UpdateOrgSettingsRequest): Promise<OrganizationSettings>

// Admin APIs (Superuser)
adminApi.createTenant(data: CreateTenantRequest): Promise<Tenant>
adminApi.listTenants(): Promise<Tenant[]>
adminApi.getTenant(id: string): Promise<Tenant>
adminApi.updateTenant(id: string, data: UpdateTenantRequest): Promise<Tenant>
adminApi.deleteTenant(id: string): Promise<void>
adminApi.activateTenant(id: string): Promise<void>
adminApi.suspendTenant(id: string): Promise<void>
```

---

## State Management Specifications

### Auth Store (Zustand)

**State Shape:**
```typescript
interface AuthState {
  // State
  user: User | null
  access_token: string | null
  refresh_token: string | null
  isAuthenticated: boolean

  // Actions
  setAuth: (tokens: { access: string; refresh: string }, user: User) => void
  setUser: (user: User) => void
  logout: () => void
  updateUser: (updates: Partial<User>) => void
}
```

**Persistence:** Use Zustand's persist middleware with localStorage

**Derived Selectors (Hooks):**
```typescript
useUser() // Returns current user
useIsAuthenticated() // Returns boolean
useIsTenantAdmin() // Returns boolean (checks is_tenant_admin or is_superuser)
useIsSuperuser() // Returns boolean
useHasRole(roleName: string) // Returns boolean
useHasPermission(permission: string) // Returns boolean
```

---

### UI Store (Zustand)

**State Shape:**
```typescript
interface UIState {
  // Sidebar
  sidebarOpen: boolean
  toggleSidebar: () => void
  closeSidebar: () => void

  // Modals
  activeModal: string | null
  openModal: (modalId: string, data?: any) => void
  closeModal: () => void
  modalData: any

  // Toast/Notifications
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void

  // Theme (future)
  theme: 'light' | 'dark'
  setTheme: (theme: 'light' | 'dark') => void
}
```

---

## Component Design Specifications

### Design System

**Color Palette (Tailwind Custom):**
```javascript
colors: {
  primary: {
    50: '#f0f9ff',
    100: '#e0f2fe',
    200: '#bae6fd',
    300: '#7dd3fc',
    400: '#38bdf8',
    500: '#0ea5e9',  // Main primary color
    600: '#0284c7',
    700: '#0369a1',
    800: '#075985',
    900: '#0c4a6e',
  },
  success: {
    500: '#10b981',
    600: '#059669',
  },
  warning: {
    500: '#f59e0b',
    600: '#d97706',
  },
  danger: {
    500: '#ef4444',
    600: '#dc2626',
  },
}
```

**Typography:**
- Headings: `font-semibold text-gray-900`
- Body: `text-gray-600`
- Small: `text-sm text-gray-500`
- Mono (for data): `font-mono text-sm`

**Spacing:**
- Card padding: `p-6` or `px-4 py-5 sm:p-6`
- Section gaps: `space-y-6` or `gap-6`
- Form gaps: `space-y-4`

**Border Radius:**
- Buttons: `rounded-md`
- Inputs: `rounded-md`
- Cards: `rounded-lg`
- Modals: `rounded-xl`

---

### Reusable Components Specifications

#### Button Component
**Variants:** primary, secondary, danger, success, ghost
**Sizes:** sm, md, lg
**States:** loading, disabled
**Features:** Left icon, right icon, full width

#### Input Component
**Features:** Label, error message, helper text, left icon, right icon (password toggle)
**States:** error, disabled, focused

#### Modal Component
**Features:** Title, body, footer, close on backdrop click, close on escape, animation
**Sizes:** sm, md, lg, xl

#### Table Component
**Features:** Sortable columns, selectable rows, pagination, loading state, empty state

#### Pagination Component
**Features:** Page numbers, previous/next, page size selector, total records display

#### Confirm Dialog Component
**Features:** Title, message, confirm text, cancel text, variant (danger/warning/info)

---

## Permission & Access Control

### Role Definitions

**Superuser:**
- Platform-level access
- Manage all tenants
- Access `/admin/*` routes

**Admin (Tenant):**
- Full tenant management
- User management (CRUD)
- Role management
- Attendance management (all users)
- Organization settings
- Invitations

**HR (Tenant):**
- User management (view, create, no delete)
- Attendance management (all users)
- Invitations
- View reports

**Employee (Tenant):**
- Own profile only
- Own attendance only
- Check-in/check-out

### Protected Route Component

**Props:**
```typescript
interface ProtectedRouteProps {
  children: React.ReactNode
  requireSuperuser?: boolean        // Must be superuser
  requireTenantAdmin?: boolean      // Must be admin or superuser
  requireHR?: boolean               // Must be HR or admin or superuser
  requireRole?: string              // Must have specific role
  requireAnyRole?: string[]         // Must have at least one of these roles
  requirePermission?: string        // Must have specific permission (future)
}
```

**Behavior:**
- Check authentication
- Check role requirements
- Redirect to `/unauthorized` if not authorized
- Redirect to `/login` if not authenticated

---

## Error Handling

### Error Boundary
**Features:**
- Catch render errors
- Display friendly error message
- Reload page button
- Report to error tracking (future)

### API Error Handling
**Types of Errors:**
1. **Validation Errors (400)** - Display field-specific errors
2. **Authentication Errors (401)** - Redirect to login, clear tokens
3. **Authorization Errors (403)** - Show "access denied" message
4. **Not Found (404)** - Show "not found" message
5. **Server Errors (500)** - Show generic error message
6. **Network Errors** - Show "connection error" message

**Error Display:**
- Toast notifications for action failures
- Inline errors for form validation
- Error pages for route-level errors
- Alert banners for global errors

---

## Responsive Design

### Breakpoints (Tailwind default):
- Mobile: `< 640px` (default)
- Tablet: `640px - 1024px` (sm, md)
- Desktop: `> 1024px` (lg, xl, 2xl)

### Mobile Adaptations:
- Collapsible sidebar (hamburger menu)
- Stack tables on mobile or use horizontal scroll
- Full-width buttons on mobile
- Bottom navigation for key actions (alternative to sidebar)
- Touch-friendly targets (min 44px height)

---

## Loading States

### Types:
1. **Skeleton Loaders** - For lists, tables
2. **Spinner Loaders** - For buttons, small sections
3. **Full Page Loader** - For initial app load, route transitions
4. **Progressive Loading** - For images, large data sets

### Implementation:
- Use React Query's `isLoading` and `isFetching` states
- Show skeleton during initial load
- Show spinner during refresh/refetch
- Maintain UI stability (avoid layout shift)

---

## Notification System

### Toast Notifications
**Types:** success, error, warning, info
**Features:** Auto-dismiss, manual dismiss, icon, action button
**Position:** Top-right or bottom-right

**Usage Examples:**
- "User created successfully"
- "Invitation sent to user@example.com"
- "Failed to update user"
- "Checked in at 9:00 AM"

---

## Form Validation

### Zod Schemas

**Email Schema:**
```typescript
emailSchema = z.string().email('Invalid email address')
```

**Password Schema:**
```typescript
passwordSchema = z.string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/[0-9]/, 'Password must contain at least one number')
```

**Login Schema:**
```typescript
loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'Password is required'),
})
```

**Create User Schema:**
```typescript
createUserSchema = z.object({
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  email: emailSchema,
  password: passwordSchema,
  phone: z.string().optional(),
  role_names: z.array(z.string()).min(1, 'At least one role is required'),
})
```

---

## Routing Structure

```typescript
// Public Routes
/login
/forgot-password
/reset-password/:uid/:token
/accept-invite/:token

// Protected Routes (Dashboard Layout)
/dashboard
/users
/users/:id
/attendance
/attendance/report
/invitations
/roles
/organization
/organization/settings
/settings
/profile

// Admin Routes (Superuser only, Admin Layout)
/admin
/admin/tenants
/admin/tenants/:id

// Error Routes
/unauthorized
/404
```

---

## Internationalization (i18n) Preparation

**Note:** Initially build in English, but structure for future i18n support
- Extract all text to constants or separate files
- Use date-fns for localized dates
- Use number formatting for currency, percentages
- Support timezone display

---

## Performance Optimizations

1. **Code Splitting:**
   - Lazy load pages with React.lazy()
   - Split vendor chunks
   - Dynamic imports for heavy libraries

2. **Image Optimization:**
   - Lazy load images below fold
   - Use WebP format when possible
   - Implement placeholder/blur effect

3. **Data Fetching:**
   - Use React Query's caching efficiently
   - Implement optimistic updates
   - Use pagination for large lists

4. **Bundle Size:**
   - Tree-shaking for unused code
   - Analyze bundle size
   - Use lightweight alternatives where possible

---

## Accessibility (a11y)

**Requirements:**
- Semantic HTML
- ARIA labels for interactive elements
- Keyboard navigation support
- Focus management in modals
- Screen reader friendly error messages
- Color contrast compliance (WCAG AA)
- Skip to main content link

**Tools:**
- ESLint plugin: jsx-a11y
- Test with keyboard only
- Test with screen reader (NVDA, JAWS)

---

## Testing Requirements

**Unit Tests:**
- Utility functions
- Custom hooks
- Component logic

**Integration Tests:**
- API service functions
- Form submissions
- Navigation flows

**E2E Tests (Playwright/Cypress):**
- Critical user flows:
  - Login
  - Check-in/out
  - Create user
  - Send invitation
  - Change password

---

## Security Considerations

1. **XSS Prevention:**
   - React's built-in escaping
   - Avoid `dangerouslySetInnerHTML`
   - Sanitize user-generated content

2. **CSRF Protection:**
   - Backend should implement CSRF tokens
   - Include CSRF token in requests

3. **Token Storage:**
   - Development: localStorage
   - Production: httpOnly cookies (consider)

4. **Sensitive Data:**
   - Don't log passwords/tokens
   - Clear sensitive data from memory
   - Use HTTPS in production

---

## Development Workflow

1. **Setup:**
   - Initialize project with Vite + React + TypeScript
   - Install all dependencies
   - Configure TailwindCSS
   - Setup ESLint and Prettier

2. **Foundation First:**
   - API client with interceptors
   - Auth store
   - React Query provider
   - Router setup
   - Protected route component

3. **Layout Components:**
   - Layout wrapper
   - Header with user menu
   - Sidebar with navigation
   - Mobile navigation

4. **Authentication Flow:**
   - Login page
   - Protected routes
   - Logout functionality
   - Token refresh

5. **Core Features:**
   - Dashboard
   - User management
   - Attendance tracking
   - Invitations

6. **Admin Features:**
   - Role management
   - Organization settings
   - Tenant management (superuser)

7. **Polish:**
   - Error handling
   - Loading states
   - Notifications
   - Responsive design

---

## Deliverables Checklist

### Pages (Complete Implementation)
- [ ] Login Page
- [ ] Forgot Password Page
- [ ] Reset Password Page
- [ ] Accept Invitation Page
- [ ] Dashboard
- [ ] Users List Page
- [ ] User Detail Page
- [ ] Attendance Page
- [ ] Attendance Report Page
- [ ] Invitations Page
- [ ] Roles Page
- [ ] Organization Overview
- [ ] Organization Settings
- [ ] Profile Page
- [ ] Admin Tenants Page
- [ ] Unauthorized Page
- [ ] Not Found Page

### Components (Complete Implementation)
- [ ] LoginForm
- [ ] ForgotPasswordForm
- [ ] ResetPasswordForm
- [ ] AcceptInviteForm
- [ ] AttendanceActions (Check In/Out Widget)
- [ ] UserList with Table
- [ ] UserForm (Create/Edit Modal)
- [ ] UserRoleManager
- [ ] AttendanceList
- [ ] AttendanceReport
- [ ] AttendanceCalendar
- [ ] InvitationForm
- [ ] InvitationList
- [ ] RoleList
- [ ] RoleForm
- [ ] OrganizationOverview
- [ ] OrganizationSettings
- [ ] TenantList (Admin)
- [ ] TenantForm (Admin)
- [ ] Header with User Menu
- [ ] Sidebar with Navigation
- [ ] Mobile Navigation
- [ ] ProtectedRoute
- [ ] ErrorBoundary
- [ ] Modal (Reusable)
- [ ] ConfirmDialog (Reusable)
- [ ] LoadingSpinner (Reusable)
- [ ] Button (Reusable)
- [ ] Input (Reusable)
- [ ] Select (Reusable)

### Core Infrastructure
- [ ] API Client with interceptors
- [ ] Complete API service functions
- [ ] Auth Store (Zustand)
- [ ] UI Store (Zustand)
- [ ] React Query setup
- [ ] Router configuration
- [ ] Protected routes
- [ ] Error handling utilities
- [ ] Custom hooks (useApiError, useAuth, usePermission)

### Features
- [ ] Authentication flow (login, logout, token refresh)
- [ ] Multi-tenancy via subdomain (Host header handling)
- [ ] Role-based access control
- [ ] Permission checking
- [ ] Form validation (Zod)
- [ ] API error handling
- [ ] Toast notifications
- [ ] Pagination
- [ ] Search and filtering
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Loading states
- [ ] Empty states
- [ ] Confirmation dialogs for destructive actions

### Documentation
- [ ] README with setup instructions
- [ ] Environment variables template
- [ ] Component documentation
- [ ] API integration guide

---

## Important Notes

1. **Multi-Tenancy**: This is the most critical architectural aspect. Every API request must include the correct `Host` header based on the current subdomain.

2. **Type Safety**: Use TypeScript strictly. No `any` types except for well-documented exceptions. Define all types in `types/` directory.

3. **API-First Design**: All data must flow through React Query. No direct setState from API responses. Use React Query's mutations and queries.

4. **Error Boundaries**: Wrap the entire app in ErrorBoundary. Also wrap individual sections if needed.

5. **Progressive Enhancement**: Start with core functionality. Add advanced features (animations, charts) after core is working.

6. **Mobile-First**: Design for mobile first, then enhance for tablet and desktop.

7. **Accessibility**: Test with keyboard. Use semantic HTML. Add ARIA labels where needed.

8. **Performance**: Use React.lazy() for code splitting. Optimize images. Use React Query's caching.

9. **Security**: Never store sensitive data in state. Clear tokens on logout. Validate on both client and server.

10. **Testing**: Write tests for critical flows. Test error cases. Test edge cases.

---

## Example Complete Component Structure

```typescript
// Example: UserList.tsx
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { userApi } from '@/lib/api'
import { useApiError } from '@/hooks/useApiError'
import { Button } from '@/components/common/Button'
import { Input } from '@/components/common/Input'
import { Table } from '@/components/common/Table'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { CreateUserModal } from './UserForm'
import type { User } from '@/types'

export function UserList() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [userToDelete, setUserToDelete] = useState<User | null>(null)

  const queryClient = useQueryClient()
  const { getErrorMessage } = useApiError()

  const { data, isLoading, error } = useQuery({
    queryKey: ['users', page, search, statusFilter],
    queryFn: () => userApi.list({
      page,
      page_size: 20,
      search: search || undefined,
      is_active: statusFilter === 'all' ? undefined : statusFilter === 'active',
    }),
  })

  const deleteMutation = useMutation({
    mutationFn: userApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setUserToDelete(null)
      // Show success toast
    },
    onError: (error) => {
      // Show error toast with getErrorMessage(error)
    },
  })

  const columns = [
    // Define columns
  ]

  return (
    <div className="space-y-6">
      {/* Header with actions */}
      {/* Filters */}
      {/* Table with pagination */}
      {/* Create modal */}
      {/* Delete confirmation dialog */}
    </div>
  )
}
```

---

## Final Instructions

1. **Build incrementally**: Start with auth and layout, then add features one by one.

2. **Test as you go**: Test each feature before moving to the next.

3. **Follow the exact folder structure**: This ensures maintainability.

4. **Use TypeScript strictly**: Define all types, avoid `any`.

5. **Implement all error cases**: Don't just handle success cases.

6. **Make it responsive**: Test on mobile, tablet, desktop.

7. **Add loading states**: Don't leave users guessing.

8. **Use semantic HTML**: Good for accessibility and SEO.

9. **Write clean code**: Follow React best practices, use composition.

10. **Think about the user**: Make the interface intuitive and friendly.

---

This prompt contains everything needed to build a complete, production-ready HRM SaaS frontend. Follow it closely and implement all specified features, pages, and components. The resulting application should be fully functional with proper error handling, responsive design, and a polished user experience.
