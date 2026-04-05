# Filtering and Search API Reference

This document describes the filtering, searching, and ordering capabilities available across all API endpoints.

## Global Configuration

All endpoints use:
- **Pagination**: `PageNumberPagination` with `PAGE_SIZE=20`
- **Filter Backend**: `DjangoFilterBackend`
- **Search**: `SearchFilter` for text-based searching
- **Ordering**: `OrderingFilter` for sorting results

---

## Authentication Endpoints (`/api/v1/auth/`)

No filtering available on authentication endpoints.

---

## User Management Endpoints (`/api/v1/users/`)

### List Users
**Endpoint**: `GET /api/v1/users/`

### Filters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `email` | string | Exact email match (case-insensitive) | `?email=john@example.com` |
| `email_contains` | string | Partial email match | `?email_contains=@example.com` |
| `first_name` | string | Exact first name match | `?first_name=John` |
| `first_name_contains` | string | Partial first name match | `?first_name_contains=Jo` |
| `last_name` | string | Exact last name match | `?last_name=Doe` |
| `last_name_contains` | string | Partial last name match | `?last_name_contains=Do` |
| `name` | string | Search first and last name | `?name=John` |
| `phone` | string | Partial phone match | `?phone=+123` |
| `is_active` | boolean | Active status | `?is_active=true` |
| `is_tenant_admin` | boolean | Tenant admin status | `?is_tenant_admin=false` |
| `is_staff` | boolean | Django staff status | `?is_staff=true` |
| `role` | string | Exact role name | `?role=HR` |
| `role_contains` | string | Partial role name | `?role_contains=Manager` |
| `joined_after` | date | Join date after (YYYY-MM-DD) | `?joined_after=2026-01-01` |
| `joined_before` | date | Join date before (YYYY-MM-DD) | `?joined_before=2026-12-31` |
| `joined_date` | date | Exact join date | `?joined_date=2026-04-05` |
| `last_login_after` | datetime | Last login after (ISO 8601) | `?last_login_after=2026-04-01T00:00:00Z` |
| `last_login_before` | datetime | Last login before (ISO 8601) | `?last_login_before=2026-04-30T23:59:59Z` |
| `last_login_days` | integer | Last login within X days ago | `?last_login_days=30` |
| `never_logged_in` | boolean | Users who never logged in | `?never_logged_in=true` |
| `search` | string | Global search | `?search=john` |

### Search Fields
`email`, `first_name`, `last_name`, `phone`

### Ordering Fields
`email`, `date_joined`, `last_login`, `first_name`, `last_name`

**Default Ordering**: `-date_joined` (newest first)

### Examples

```bash
# Get all active users
GET /api/v1/users/?is_active=true

# Get users with role HR
GET /api/v1/users/?role=HR

# Get users who joined in April 2026
GET /api/v1/users/?joined_after=2026-04-01&joined_before=2026-04-30

# Get users who logged in within last 7 days
GET /api/v1/users/?last_login_days=7

# Search users by name or email
GET /api/v1/users/?search=john

# Order by last login
GET /api/v1/users/?ordering=-last_login
```

---

## Role Management Endpoints (`/api/v1/roles/`)

### List Roles
**Endpoint**: `GET /api/v1/roles/`

### Filters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `name` | string | Exact role name (case-insensitive) | `?name=HR` |
| `name_contains` | string | Partial role name | `?name_contains=Manager` |
| `is_system_role` | boolean | System role flag | `?is_system_role=false` |
| `description` | string | Partial description match | `?description=access` |
| `search` | string | Global search | `?search=admin` |

### Search Fields
`name`, `description`

### Ordering Fields
`name`, `created_at`

**Default Ordering**: `name` (alphabetical)

---

## Attendance Endpoints (`/api/v1/attendance/`)

### List Attendance Records
**Endpoint**: `GET /api/v1/attendance/`

### Filters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | date | Exact date match (YYYY-MM-DD) | `?date=2026-04-05` |
| `date_gte` | date | Date from (inclusive) | `?date_gte=2026-04-01` |
| `date_lte` | date | Date to (inclusive) | `?date_lte=2026-04-30` |
| `status` | string | Attendance status (multiple) | `?status=present&status=late` |
| `user` | UUID | User ID | `?user=123e4567-e89b-12d3-a456-426614174000` |
| `user_email` | string | User email (exact) | `?user_email=john@example.com` |
| `user_email_contains` | string | User email (partial) | `?user_email_contains=@example.com` |
| `month` | integer | Month number (1-12) | `?month=4` |
| `year` | integer | Year (YYYY) | `?year=2026` |
| `has_checkin` | boolean | Has check-in time | `?has_checkin=true` |
| `has_checkout` | boolean | Has check-out time | `?has_checkout=false` |
| `checkin_time_after` | datetime | Check-in after (ISO 8601) | `?checkin_time_after=2026-04-01T09:00:00Z` |
| `checkin_time_before` | datetime | Check-in before (ISO 8601) | `?checkin_time_before=2026-04-30T18:00:00Z` |
| `today` | boolean | Today's records only | `?today=true` |
| `this_week` | boolean | This week's records only | `?this_week=true` |
| `this_month` | boolean | This month's records only | `?this_month=true` |
| `search` | string | Global search | `?search=john` |

### Status Choices
- `present` - Present
- `absent` - Absent
- `half_day` - Half Day
- `late` - Late

### Search Fields
`user__email`, `user__first_name`, `user__last_name`, `notes`

### Ordering Fields
`date`, `checkin_time`, `checkout_time`, `created_at`

**Default Ordering**: `-date, -checkin_time` (newest date and check-in first)

### Examples

```bash
# Get today's attendance
GET /api/v1/attendance/?today=true

# Get attendance for April 2026
GET /api/v1/attendance/?month=4&year=2026

# Get attendance for specific user in date range
GET /api/v1/attendance/?user_email=john@example.com&date_gte=2026-04-01&date_lte=2026-04-30

# Get all late attendance records
GET /api/v1/attendance/?status=late

# Get users who haven't checked out
GET /api/v1/attendance/?has_checkin=true&has_checkout=false

# Get this week's attendance
GET /api/v1/attendance/?this_week=true

# Search attendance by user name or notes
GET /api/v1/attendance/?search=john
```

### My Attendance Endpoint
**Endpoint**: `GET /api/v1/attendance/my-attendance/`

### Filters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `start_date` | date | Start date (YYYY-MM-DD) | `?start_date=2026-04-01` |
| `end_date` | date | End date (YYYY-MM-DD) | `?end_date=2026-04-30` |

**Note**: This endpoint uses custom date filtering (not filterset class).

### My Monthly Stats Endpoint
**Endpoint**: `GET /api/v1/attendance/my-monthly-stats/`

### Filters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `month` | integer | Month number (1-12) | `?month=4` |
| `year` | integer | Year (YYYY) | `?year=2026` |

**Note**: Returns aggregated statistics, not a list.

---

## Invitation Endpoints (`/api/v1/invite/`)

### List Invitations
**Endpoint**: `GET /api/v1/invite/`

### Filters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `email` | string | Exact email (case-insensitive) | `?email=john@example.com` |
| `email_contains` | string | Partial email | `?email_contains=@example.com` |
| `status` | string | Invitation status (multiple) | `?status=pending` |
| `first_name` | string | Partial first name | `?first_name=John` |
| `last_name` | string | Partial last name | `?last_name=Doe` |
| `invited_by` | UUID | Inviter user ID | `?invited_by=...` |
| `invited_by_email` | string | Inviter email (partial) | `?invited_by_email=admin@...` |
| `created_after` | date | Created after (YYYY-MM-DD) | `?created_after=2026-04-01` |
| `created_before` | date | Created before (YYYY-MM-DD) | `?created_before=2026-04-30` |
| `created_days` | integer | Created within X days ago | `?created_days=7` |
| `expires_after` | date | Expires after (YYYY-MM-DD) | `?expires_after=2026-04-01` |
| `expires_before` | date | Expires before (YYYY-MM-DD) | `?expires_before=2026-04-30` |
| `is_expired` | boolean | Filter expired | `?is_expired=true` |
| `is_valid` | boolean | Filter valid (pending & not expired) | `?is_valid=true` |
| `accepted_after` | date | Accepted after (YYYY-MM-DD) | `?accepted_after=2026-04-01` |
| `accepted_before` | date | Accepted before (YYYY-MM-DD) | `?accepted_before=2026-04-30` |
| `search` | string | Global search | `?search=john` |

### Status Choices
- `pending` - Pending acceptance
- `accepted` - Accepted
- `cancelled` - Cancelled
- `expired` - Expired

### Search Fields
`email`, `first_name`, `last_name`

### Ordering Fields
`created_at`, `expires_at`, `accepted_at`

**Default Ordering**: `-created_at` (newest first)

### Examples

```bash
# Get all pending invitations
GET /api/v1/invite/?status=pending

# Get expired invitations
GET /api/v1/invite/?is_expired=true

# Get valid (pending and not expired) invitations
GET /api/v1/invite/?is_valid=true

# Get invitations created in last 7 days
GET /api/v1/invite/?created_days=7

# Get invitations sent by specific user
GET /api/v1/invite/?invited_by_email=admin@example.com
```

---

## Audit Log Endpoints (`/api/v1/audit/`)

### List Audit Logs
**Endpoint**: `GET /api/v1/audit/`

**Permission**: Tenant Admin only

### Filters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `action` | string | Exact action | `?action=user.login` |
| `action_contains` | string | Partial action | `?action_contains=user.created` |
| `user` | UUID | User ID | `?user=...` |
| `user_email` | string | User email (partial) | `?user_email=john@example.com` |
| `target_model` | string | Target model (exact) | `?target_model=User` |
| `target_model_contains` | string | Target model (partial) | `?target_model_contains=User` |
| `target_id` | string | Target object ID (partial) | `?target_id=123` |
| `timestamp_after` | datetime | Timestamp after (ISO 8601) | `?timestamp_after=2026-04-01T00:00:00Z` |
| `timestamp_before` | datetime | Timestamp before (ISO 8601) | `?timestamp_before=2026-04-30T23:59:59Z` |
| `timestamp_date` | date | Timestamp date (YYYY-MM-DD) | `?timestamp_date=2026-04-05` |
| `timestamp_days` | integer | Within X days ago | `?timestamp_days=7` |
| `ip_address` | string | IP address (partial) | `?ip_address=192.168` |
| `search` | string | Global search | `?search=login` |

### Search Fields
`action`, `target_model`, `target_id`, `user__email`, `ip_address`

### Ordering Fields
`timestamp`, `action`

**Default Ordering**: `-timestamp` (newest first)

### Examples

```bash
# Get all user login logs
GET /api/v1/audit/?action=user.login

# Get logs for specific user
GET /api/v1/audit/?user_email=john@example.com

# Get logs from last 7 days
GET /api/v1/audit/?timestamp_days=7

# Get logs for User model
GET /api/v1/audit/?target_model=User

# Get logs from specific IP
GET /api/v1/audit/?ip_address=192.168.1.1
```

---

## Organization/Tenant Endpoints (`/api/v1/admin/tenants/`)

**Permission**: Superuser only

### Filters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `name` | string | Exact name (case-insensitive) | `?name=Acme` |
| `name_contains` | string | Partial name | `?name_contains=Corp` |
| `slug` | string | Exact slug (case-insensitive) | `?slug=acme` |
| `slug_contains` | string | Partial slug | `?slug_contains=acme` |
| `status` | string | Organization status (multiple) | `?status=active` |
| `timezone` | string | Exact timezone | `?timezone=America/New_York` |
| `timezone_contains` | string | Partial timezone | `?timezone_contains=America` |
| `created_after` | date | Created after (YYYY-MM-DD) | `?created_after=2026-01-01` |
| `created_before` | date | Created before (YYYY-MM-DD) | `?created_before=2026-12-31` |
| `created_days` | integer | Created within X days ago | `?created_days=30` |
| `public_signup_enabled` | boolean | Public signup flag | `?public_signup_enabled=false` |
| `search` | string | Global search | `?search=acme` |

### Status Choices
- `active` - Active
- `suspended` - Suspended
- `pending` - Pending

### Search Fields
`name`, `slug`

### Ordering Fields
`name`, `created_at`, `status`

**Default Ordering**: `-created_at` (newest first)

---

## Common Patterns

### Pagination

All list endpoints support pagination:

```bash
# Get first page (default page size: 20)
GET /api/v1/users/

# Get specific page
GET /api/v1/users/?page=2

# Change page size
GET /api/v1/users/?page=1&page_size=50
```

### Combining Filters

Multiple filters can be combined:

```bash
# Get active HR users who joined in April
GET /api/v1/users/?role=HR&is_active=true&joined_after=2026-04-01&joined_before=2026-04-30

# Get attendance for specific user in date range with status
GET /api/v1/attendance/?user_email=john@example.com&date_gte=2026-04-01&date_lte=2026-04-30&status=present
```

### Ordering

Use `ordering` parameter with `-` prefix for descending order:

```bash
# Ascending order
GET /api/v1/users/?ordering=email

# Descending order
GET /api/v1/users/?ordering=-email

# Multiple order fields
GET /api/v1/users/?ordering=-last_login,first_name
```

### Search

Global search across multiple fields:

```bash
# Search users by any of: email, first_name, last_name, phone
GET /api/v1/users/?search=john

# Search attendance by any of: user email, user names, notes
GET /api/v1/attendance/?search=meeting
```

---

## Leaves Filtering

### Filter Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `status` | Multiple Choice | Filter by leave status | `?status=pending&status=approved` |
| `employee` | UUID | Filter by employee ID | `?employee=5375cf8f-b9eb-40b6-8c91-0f614507f1e2` |
| `employee_email` | String | Filter by employee email (exact) | `?employee_email=john@example.com` |
| `employee_email_contains` | String | Filter by employee email (partial) | `?employee_email_contains=john` |
| `leave_type` | Multiple Choice | Filter by leave type | `?leave_type=casual&leave_type=sick` |
| `start_date_gte` | Date | Start date from (YYYY-MM-DD) | `?start_date_gte=2026-04-01` |
| `start_date_lte` | Date | Start date to (YYYY-MM-DD) | `?start_date_lte=2026-04-30` |
| `end_date_gte` | Date | End date from (YYYY-MM-DD) | `?end_date_gte=2026-04-01` |
| `end_date_lte` | Date | End date to (YYYY-MM-DD) | `?end_date_lte=2026-04-30` |
| `approved_by` | UUID | Filter by approver ID | `?approved_by=5375cf8f-b9eb-40b6-8c91-0f614507f1e2` |
| `created_after` | Date | Created after date | `?created_after=2026-04-01` |
| `created_before` | Date | Created before date | `?created_before=2026-04-30` |
| `month` | Number | Filter by month (1-12) | `?month=4` |
| `year` | Number | Filter by year | `?year=2026` |
| `search` | String | Search in reason, employee name/email | `?search=vacation` |

### Status Choices
- `pending` - Pending approval
- `approved` - Approved
- `rejected` - Rejected
- `cancelled` - Cancelled

### Leave Type Choices
- `casual` - Casual Leave
- `sick` - Sick Leave
- `earned` - Earned Leave
- `unpaid` - Unpaid Leave
- `maternity` - Maternity Leave
- `paternity` - Paternity Leave
- `comp_off` - Compensatory Off

### Examples

```bash
# Get all pending leaves
GET /api/v1/leaves/?status=pending

# Get leaves for a specific employee
GET /api/v1/leaves/?employee_email=john@example.com

# Get casual and sick leaves for April 2026
GET /api/v1/leaves/?leave_type=casual&leave_type=sick&start_date_gte=2026-04-01&start_date_lte=2026-04-30

# Get leaves created in the last 7 days
GET /api/v1/leaves/?created_after=2026-03-29

# Get approved leaves for current year
GET /api/v1/leaves/?status=approved&year=2026

# Search for leave requests with specific reason
GET /api/v1/leaves/?search=vacation
```

### Ordering

Supported ordering fields:
- `start_date` / `-start_date`
- `-created_at` (default)
- `status`

```bash
# Order by start date (newest first)
GET /api/v1/leaves/?ordering=-start_date

# Order by creation date (oldest first)
GET /api/v1/leaves/?ordering=created_at
```

---

## Leave Balances Filtering

### Filter Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `employee` | UUID | Filter by employee ID | `?employee=5375cf8f-b9eb-40b6-8c91-0f614507f1e2` |
| `employee_email` | String | Filter by employee email (exact) | `?employee_email=john@example.com` |
| `leave_type` | Multiple Choice | Filter by leave type | `?leave_type=casual` |
| `year` | Number | Filter by year | `?year=2026` |
| `has_balance` | Boolean | Filter by positive balance | `?has_balance=true` |

### Examples

```bash
# Get all leave balances for 2026
GET /api/v1/leaves/balances/?year=2026

# Get casual leave balances for all employees
GET /api/v1/leaves/balances/?leave_type=casual&year=2026

# Get employees with positive casual leave balance
GET /api/v1/leaves/balances/?leave_type=casual&has_balance=true

# Get specific employee's balances
GET /api/v1/leaves/balances/?employee_email=john@example.com
```

---

## Notifications Filtering

### Filter Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `is_read` | Boolean | Filter by read status | `?is_read=false` |
| `notification_type` | Multiple Choice | Filter by notification type | `?notification_type=leave_applied` |
| `created_after` | Date | Created after date | `?created_after=2026-04-01` |
| `created_before` | Date | Created before date | `?created_before=2026-04-30` |
| `search` | String | Search in title and message | `?search=approved` |

### Notification Type Choices
- `leave_applied` - New leave application
- `leave_approved` - Leave approved
- `leave_rejected` - Leave rejected
- `leave_cancelled` - Leave cancelled
- `checkin` - User checked in
- `checkout` - User checked out
- `user_created` - New user created
- `role_assigned` - Role assigned
- `mention` - User mentioned
- `system` - System notification
- `info` - General information

### Examples

```bash
# Get all unread notifications
GET /api/v1/notifications/?is_read=false

# Get leave-related notifications
GET /api/v1/notifications/?notification_type=leave_applied&notification_type=leave_approved

# Get recent notifications (last 7 days)
GET /api/v1/notifications/?created_after=2026-03-29

# Search for specific notifications
GET /api/v1/notifications/?search=approved

# Get unread leave notifications
GET /api/v1/notifications/?is_read=false&notification_type=leave_approved
```

### Ordering

Supported ordering fields:
- `created_at` / `-created_at` (default: `-created_at`)
- `is_read`

```bash
# Order by creation date (oldest first)
GET /api/v1/notifications/?ordering=created_at

# Order by read status
GET /api/v1/notifications/?ordering=is_read
```

---

## Response Format

Paginated responses include:

```json
{
  "count": 150,
  "next": "http://api.example.com/api/v1/users/?page=2",
  "previous": null,
  "results": [
    { ... },
    { ... }
  ]
}
```

---

## Performance Tips

1. **Use specific filters** instead of global search when possible
   - `?email=john@example.com` is faster than `?search=john@example.com`

2. **Add pagination** for large result sets
   - Always use `?page=N` or `?page_size=N`

3. **Use date ranges** instead of fetching all records
   - `?date_gte=2026-04-01&date_lte=2026-04-30`

4. **Limit ordering fields** to those with indexes
   - See model indexes in `models.py`

5. **Use boolean filters** for presence checks
   - `?has_checkin=true` instead of filtering client-side

---

## Error Handling

Invalid filter values return `400 Bad Request`:

```json
{
  "detail": "Invalid date format. Use YYYY-MM-DD."
}
```

Invalid ordering fields return `400 Bad Request`:

```json
{
  "detail": "Invalid ordering field. Valid fields: email, date_joined, last_login, first_name, last_name"
}
```
