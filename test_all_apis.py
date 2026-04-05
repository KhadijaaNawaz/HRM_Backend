#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive API Testing Script for HRM SaaS Application
Tests all API endpoints systematically to ensure smooth flow
"""

import sys
import io
import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test credentials (from existing test data)
SUPERUSER_EMAIL = "superadmin@hrmsaas.com"
SUPERUSER_PASSWORD = "SuperAdmin123!"

# Storage for test data
test_data = {
    "tokens": {},
    "tenants": {},
    "users": {},
    "roles": {},
    "invitations": {},
    "attendance": {}
}

# Colors for output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def print_success(message: str):
    print(f"{Colors.GREEN}[PASS] {message}{Colors.RESET}")

def print_error(message: str):
    print(f"{Colors.RED}[FAIL] {message}{Colors.RESET}")

def print_info(message: str):
    print(f"{Colors.BLUE}[INFO] {message}{Colors.RESET}")

def print_section(title: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_test(name: str):
    print(f"{Colors.YELLOW}Testing: {name}{Colors.RESET}")

# HTTP Methods
def api_request(method: str, endpoint: str, token: Optional[str] = None,
                data: Optional[Dict] = None, params: Optional[Dict] = None,
                tenant_id: Optional[str] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
    """Make API request with proper headers"""
    url = f"{API_BASE}{endpoint}"
    headers = headers or {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, params=params, timeout=10)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data, params=params, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, params=params, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, params=params, timeout=10)
        else:
            return {"success": False, "error": f"Unknown method: {method}"}

        try:
            return {
                "success": response.status_code < 400,
                "status": response.status_code,
                "data": response.json() if response.content else None,
                "response": response
            }
        except json.JSONDecodeError:
            return {
                "success": response.status_code < 400,
                "status": response.status_code,
                "data": response.text,
                "response": response
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# TEST SUITE 1: AUTHENTICATION
# ============================================================================

def test_authentication():
    """Test all authentication endpoints"""
    print_section("AUTHENTICATION API TESTS")

    # 1.1 Test Login (requires tenant context since User is a tenant model)
    print_test("1. Login with superuser credentials")
    result = api_request("POST", "/auth/login/",
                        data={
        "email": SUPERUSER_EMAIL,
        "password": SUPERUSER_PASSWORD
    }, tenant_id="acme")  # Use existing acme tenant
    if result["success"]:
        test_data["tokens"]["superuser"] = result["data"]["access"]
        test_data["tokens"]["superuser_refresh"] = result["data"]["refresh"]
        print_success(f"Login successful! Access token: {result['data']['access'][:50]}...")
    else:
        print_error(f"Login failed: {result.get('error', result.get('data'))}")
        return False

    # 1.2 Test Get Current User
    print_test("2. Get current user info")
    result = api_request("GET", "/auth/me/", token=test_data["tokens"]["superuser"])
    if result["success"]:
        test_data["users"]["superuser"] = result["data"]
        print_success(f"Current user: {result['data']['email']}")
    else:
        print_error(f"Failed to get current user: {result.get('data')}")

    # 1.3 Test Token Refresh
    print_test("3. Refresh access token")
    result = api_request("POST", "/auth/token/refresh/", data={
        "refresh": test_data["tokens"]["superuser_refresh"]
    })
    if result["success"]:
        test_data["tokens"]["superuser"] = result["data"]["access"]
        print_success("Token refreshed successfully")
    else:
        print_error(f"Token refresh failed: {result.get('data')}")

    # 1.4 Test Password Change
    print_test("4. Change password")
    result = api_request("POST", "/auth/password/change/",
                        token=test_data["tokens"]["superuser"],
                        data={
                            "old_password": SUPERUSER_PASSWORD,
                            "new_password": "NewPassword123!",
                            "confirm_password": "NewPassword123!"
                        })
    if result["success"]:
        print_success("Password changed successfully")
        # Change it back for other tests
        api_request("POST", "/auth/password/change/",
                   token=test_data["tokens"]["superuser"],
                   data={
                       "old_password": "NewPassword123!",
                       "new_password": SUPERUSER_PASSWORD,
                       "confirm_password": SUPERUSER_PASSWORD
                   })
        print_success("Password reverted for continued testing")
    else:
        print_error(f"Password change failed: {result.get('data')}")

    # 1.5 Test Password Forgot (will fail without email backend, but tests endpoint)
    print_test("5. Request password reset email")
    result = api_request("POST", "/auth/password/forgot/", data={
        "email": SUPERUSER_EMAIL
    })
    # This might fail without email backend configured
    print_info(f"Password forgot request result: {result.get('data', 'Endpoint responded')}")

    # 1.6 Test Logout
    print_test("6. Logout")
    result = api_request("POST", "/auth/logout/",
                        token=test_data["tokens"]["superuser"],
                        data={"refresh": test_data["tokens"]["superuser_refresh"]})
    if result["success"]:
        print_success("Logout successful")
    else:
        print_error(f"Logout failed: {result.get('data')}")

    # Login again for subsequent tests
    result = api_request("POST", "/auth/login/", data={
        "email": SUPERUSER_EMAIL,
        "password": SUPERUSER_PASSWORD
    }, tenant_id="acme")
    if result["success"]:
        test_data["tokens"]["superuser"] = result["data"]["access"]
        test_data["tokens"]["superuser_refresh"] = result["data"]["refresh"]
        print_success("Logged back in for continued testing")

    return True

# ============================================================================
# TEST SUITE 2: PLATFORM ADMIN (TENANT MANAGEMENT)
# ============================================================================

def test_platform_admin():
    """Test platform admin endpoints"""
    print_section("PLATFORM ADMIN API TESTS")

    # 2.1 List all tenants
    print_test("1. List all tenants")
    result = api_request("GET", "/admin/tenants/",
                        token=test_data["tokens"]["superuser"])
    if result["success"]:
        print_success(f"Found {len(result['data'])} existing tenants")
        test_data["tenants"]["existing"] = result["data"]
    else:
        print_error(f"Failed to list tenants: {result.get('data')}")

    # 2.2 Create a new tenant
    print_test("2. Create new tenant 'testcompany'")
    tenant_slug = f"testcompany-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    result = api_request("POST", "/admin/create-tenant/",
                        token=test_data["tokens"]["superuser"],
                        data={
                            "name": f"Test Company {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                            "slug": tenant_slug,
                            "admin_email": f"admin@{tenant_slug}.com",
                            "admin_password": "TestAdmin123!",
                            "admin_first_name": "Test",
                            "admin_last_name": "Admin"
                        })
    if result["success"]:
        test_data["tenants"]["test"] = result["data"]
        test_data["tenants"]["test_slug"] = tenant_slug
        print_success(f"Tenant created: {result['data']['name']} (ID: {result['data'].get('id')})")
    else:
        print_error(f"Failed to create tenant: {result.get('data')}")
        return False

    # 2.3 Get tenant details
    print_test("3. Get tenant details")
    tenant_id = test_data["tenants"]["test"].get("id")
    result = api_request("GET", f"/admin/tenants/{tenant_id}/",
                        token=test_data["tokens"]["superuser"])
    if result["success"]:
        print_success(f"Tenant details: {result['data']['name']}")
    else:
        print_error(f"Failed to get tenant details: {result.get('data')}")

    # 2.4 Update tenant
    print_test("4. Update tenant")
    result = api_request("PUT", f"/admin/tenants/{tenant_id}/",
                        token=test_data["tokens"]["superuser"],
                        data={
                            "name": f"Updated Test Company {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        })
    if result["success"]:
        print_success(f"Tenant updated: {result['data']['name']}")
    else:
        print_error(f"Failed to update tenant: {result.get('data')}")

    # 2.5 List tenant users
    print_test("5. List tenant users")
    result = api_request("GET", f"/admin/tenants/{tenant_id}/users/",
                        token=test_data["tokens"]["superuser"])
    if result["success"]:
        print_success(f"Found {len(result['data'])} users in tenant")
        if result["data"]:
            test_data["users"]["tenant_admin"] = result["data"][0]
    else:
        print_error(f"Failed to list tenant users: {result.get('data')}")

    # 2.6 Suspend tenant
    print_test("6. Suspend tenant")
    result = api_request("POST", f"/admin/tenants/{tenant_id}/suspend/",
                        token=test_data["tokens"]["superuser"])
    if result["success"]:
        print_success(f"Tenant suspended: {result['data']['status']}")
    else:
        print_error(f"Failed to suspend tenant: {result.get('data')}")

    # 2.7 Activate tenant
    print_test("7. Activate tenant")
    result = api_request("POST", f"/admin/tenants/{tenant_id}/activate/",
                        token=test_data["tokens"]["superuser"])
    if result["success"]:
        print_success(f"Tenant activated: {result['data']['status']}")
    else:
        print_error(f"Failed to activate tenant: {result.get('data')}")

    # 2.8 List all tenants again
    print_test("8. List all tenants (verify new tenant exists)")
    result = api_request("GET", "/admin/tenants/",
                        token=test_data["tokens"]["superuser"])
    if result["success"]:
        print_success(f"Total tenants: {len(result['data'])}")
    else:
        print_error(f"Failed to list tenants: {result.get('data')}")

    return True

# ============================================================================
# TEST SUITE 3: TENANT LOGIN & USER MANAGEMENT
# ============================================================================

def test_tenant_login_and_users():
    """Test tenant-specific login and user management"""
    print_section("TENANT LOGIN & USER MANAGEMENT TESTS")

    # 3.1 Login as tenant admin
    print_test("1. Login as tenant admin")
    tenant_slug = test_data.get("tenants", {}).get("test_slug", "acme")
    result = api_request("POST", "/auth/login/",
                        data={
                            "email": f"admin@{tenant_slug}.com",
                            "password": "TestAdmin123!"
                        },
                        tenant_id=tenant_slug)
    if result["success"]:
        test_data["tokens"]["tenant_admin"] = result["data"]["access"]
        test_data["tokens"]["tenant_admin_refresh"] = result["data"]["refresh"]
        print_success("Tenant admin login successful")
    else:
        print_error(f"Tenant admin login failed: {result.get('data')}")
        return False

    # 3.2 List users
    print_test("2. List all users")
    result = api_request("GET", "/users/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success(f"Found {len(result['data'])} users")
        test_data["users"]["all"] = result["data"]
    else:
        print_error(f"Failed to list users: {result.get('data')}")

    # 3.3 Create new user
    print_test("3. Create new HR user")
    result = api_request("POST", "/users/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug,
                        data={
                            "email": f"hr.user.{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com",
                            "first_name": "HR",
                            "last_name": "User",
                            "password": "HrUser123!",
                            "phone": "+1234567890"
                        })
    if result["success"]:
        test_data["users"]["hr_user"] = result["data"]
        print_success(f"HR user created: {result['data']['email']}")
    else:
        print_error(f"Failed to create user: {result.get('data')}")

    # 3.4 Get user details
    print_test("4. Get user details")
    user_id = test_data["users"]["hr_user"]["id"]
    result = api_request("GET", f"/users/{user_id}/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success(f"User details: {result['data']['email']}")
    else:
        print_error(f"Failed to get user details: {result.get('data')}")

    # 3.5 Update user
    print_test("5. Update user")
    result = api_request("PATCH", f"/users/{user_id}/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug,
                        data={
                            "first_name": "HR Updated",
                            "phone": "+9876543210"
                        })
    if result["success"]:
        print_success(f"User updated: {result['data']['first_name']}")
    else:
        print_error(f"Failed to update user: {result.get('data')}")

    # 3.6 Create Employee user
    print_test("6. Create employee user")
    result = api_request("POST", "/users/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug,
                        data={
                            "email": f"employee.{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com",
                            "first_name": "Test",
                            "last_name": "Employee",
                            "password": "Employee123!"
                        })
    if result["success"]:
        test_data["users"]["employee"] = result["data"]
        print_success(f"Employee created: {result['data']['email']}")
    else:
        print_error(f"Failed to create employee: {result.get('data')}")

    # 3.7 Get current user profile
    print_test("7. Get current user profile")
    result = api_request("GET", "/users/me/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success(f"Current profile: {result['data']['email']}")
    else:
        print_error(f"Failed to get profile: {result.get('data')}")

    # 3.8 Update current user profile
    print_test("8. Update current user profile")
    result = api_request("PATCH", "/users/me/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug,
                        data={
                            "first_name": "Admin Updated",
                            "last_name": "User"
                        })
    if result["success"]:
        print_success(f"Profile updated: {result['data']['first_name']} {result['data']['last_name']}")
    else:
        print_error(f"Failed to update profile: {result.get('data')}")

    return True

# ============================================================================
# TEST SUITE 4: ROLE MANAGEMENT
# ============================================================================

def test_role_management():
    """Test role management endpoints"""
    print_section("ROLE MANAGEMENT API TESTS")

    tenant_slug = test_data.get("tenants", {}).get("test_slug", "acme")

    # 4.1 List all roles
    print_test("1. List all roles")
    result = api_request("GET", "/roles/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success(f"Found {len(result['data'])} roles")
        test_data["roles"]["all"] = result["data"]
        # Store system role IDs
        for role in result["data"]:
            if role["name"] == "Admin":
                test_data["roles"]["admin_id"] = role["id"]
            elif role["name"] == "HR":
                test_data["roles"]["hr_id"] = role["id"]
            elif role["name"] == "Employee":
                test_data["roles"]["employee_id"] = role["id"]
    else:
        print_error(f"Failed to list roles: {result.get('data')}")

    # 4.2 Create custom role
    print_test("2. Create custom role")
    result = api_request("POST", "/roles/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug,
                        data={
                            "name": f"Manager-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            "description": "Custom manager role"
                        })
    if result["success"]:
        test_data["roles"]["custom"] = result["data"]
        print_success(f"Custom role created: {result['data']['name']}")
    else:
        print_error(f"Failed to create role: {result.get('data')}")

    # 4.3 Get role details
    print_test("3. Get role details")
    role_id = test_data["roles"]["custom"]["id"]
    result = api_request("GET", f"/roles/{role_id}/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success(f"Role details: {result['data']['name']}")
    else:
        print_error(f"Failed to get role details: {result.get('data')}")

    # 4.4 Update role
    print_test("4. Update custom role")
    result = api_request("PATCH", f"/roles/{role_id}/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug,
                        data={
                            "description": "Updated manager role description"
                        })
    if result["success"]:
        print_success(f"Role updated: {result['data']['description']}")
    else:
        print_error(f"Failed to update role: {result.get('data')}")

    # 4.5 Assign role to user
    print_test("5. Assign HR role to user")
    hr_user_id = test_data["users"]["hr_user"]["id"]
    hr_role_id = test_data["roles"]["hr_id"]
    result = api_request("POST", f"/roles/{hr_role_id}/assign/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug,
                        data={
                            "user_id": str(hr_user_id)
                        })
    if result["success"]:
        print_success(f"HR role assigned to user")
    else:
        print_error(f"Failed to assign role: {result.get('data')}")

    # 4.6 Assign Employee role
    print_test("6. Assign Employee role to user")
    employee_id = test_data["users"]["employee"]["id"]
    employee_role_id = test_data["roles"]["employee_id"]
    result = api_request("POST", f"/roles/{employee_role_id}/assign/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug,
                        data={
                            "user_id": str(employee_id)
                        })
    if result["success"]:
        print_success(f"Employee role assigned")
    else:
        print_error(f"Failed to assign role: {result.get('data')}")

    # 4.7 Revoke role from user
    print_test("7. Revoke role from user")
    custom_role_id = test_data["roles"]["custom"]["id"]
    result = api_request("POST", f"/roles/{custom_role_id}/revoke/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug,
                        data={
                            "user_id": str(hr_user_id)
                        })
    if result["success"]:
        print_success(f"Role revoked from user")
    else:
        print_error(f"Failed to revoke role: {result.get('data')}")

    # 4.8 Try to delete system role (should fail)
    print_test("8. Try to delete system role (should fail)")
    result = api_request("DELETE", f"/roles/{hr_role_id}/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if not result["success"]:
        print_success("System role protected from deletion")
    else:
        print_error("System role was deleted (should not happen)")

    # 4.9 Delete custom role
    print_test("9. Delete custom role")
    result = api_request("DELETE", f"/roles/{custom_role_id}/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success("Custom role deleted")
    else:
        print_error(f"Failed to delete custom role: {result.get('data')}")

    return True

# ============================================================================
# TEST SUITE 5: INVITATIONS
# ============================================================================

def test_invitations():
    """Test invitation endpoints"""
    print_section("INVITATION API TESTS")

    tenant_slug = test_data.get("tenants", {}).get("test_slug", "acme")

    # 5.1 Create invitation
    print_test("1. Create invitation")
    result = api_request("POST", "/invite/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug,
                        data={
                            "email": f"invited.{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com",
                            "first_name": "Invited",
                            "last_name": "User",
                            "role_names": ["Employee"]
                        })
    if result["success"]:
        test_data["invitations"]["pending"] = result["data"]
        print_success(f"Invitation created: {result['data']['email']}")
    else:
        print_error(f"Failed to create invitation: {result.get('data')}")
        return False

    # 5.2 List invitations
    print_test("2. List invitations")
    result = api_request("GET", "/invite/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success(f"Found {len(result['data'])} invitations")
    else:
        print_error(f"Failed to list invitations: {result.get('data')}")

    # 5.3 Get invitation details
    print_test("3. Get invitation details")
    invite_id = test_data["invitations"]["pending"]["id"]
    result = api_request("GET", f"/invite/{invite_id}/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success(f"Invitation details: {result['data']['email']}")
    else:
        print_error(f"Failed to get invitation details: {result.get('data')}")

    # 5.4 Resend invitation
    print_test("4. Resend invitation")
    result = api_request("POST", f"/invite/{invite_id}/resend/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success("Invitation resent")
    else:
        print_error(f"Failed to resend invitation: {result.get('data')}")

    # 5.5 Cancel invitation
    print_test("5. Cancel invitation")
    result = api_request("POST", f"/invite/{invite_id}/cancel/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success(f"Invitation cancelled: {result['data']['status']}")
    else:
        print_error(f"Failed to cancel invitation: {result.get('data')}")

    # 5.6 Create another invitation for accept test
    print_test("6. Create invitation for accept test")
    result = api_request("POST", "/invite/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug,
                        data={
                            "email": f"accept.test.{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com",
                            "first_name": "Accept",
                            "last_name": "Test",
                            "role_names": ["HR"]
                        })
    if result["success"]:
        test_data["invitations"]["for_accept"] = result["data"]
        print_success(f"Invitation created: {result['data']['email']}")
    else:
        print_error(f"Failed to create invitation: {result.get('data')}")

    # 5.7 Test accept endpoint (public, no auth needed)
    print_test("7. Test accept invitation endpoint")
    invite_token = test_data["invitations"]["for_accept"]["token"]
    result = api_request("POST", "/invite/accept/",
                        data={
                            "token": invite_token,
                            "password": "AcceptedUser123!",
                            "confirm_password": "AcceptedUser123!"
                        })
    if result["success"]:
        print_success("Invitation accepted successfully")
    else:
        print_error(f"Failed to accept invitation: {result.get('data')}")

    return True

# ============================================================================
# TEST SUITE 6: ORGANIZATION SETTINGS
# ============================================================================

def test_organization_settings():
    """Test organization settings endpoints"""
    print_section("ORGANIZATION SETTINGS API TESTS")

    tenant_slug = test_data.get("tenants", {}).get("test_slug", "acme")

    # 6.1 Get organization overview
    print_test("1. Get organization overview")
    result = api_request("GET", "/organization/overview/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success(f"Organization overview: {result['data'].get('total_users', 'N/A')} users")
    else:
        print_error(f"Failed to get overview: {result.get('data')}")

    # 6.2 Get organization settings
    print_test("2. Get organization settings")
    result = api_request("GET", "/organization/settings/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"]:
        test_data["org_settings"] = result["data"]
        print_success(f"Organization settings: timezone {result['data'].get('timezone', 'N/A')}")
    else:
        print_error(f"Failed to get settings: {result.get('data')}")

    # 6.3 Update organization settings
    print_test("3. Update organization settings")
    result = api_request("PUT", "/organization/settings/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug,
                        data={
                            "timezone": "America/New_York",
                            "workdays": ["Mon", "Tue", "Wed", "Thu", "Fri"],
                            "monthly_required_days": 22,
                            "public_signup_enabled": False
                        })
    if result["success"]:
        print_success(f"Settings updated: timezone {result['data']['timezone']}")
    else:
        print_error(f"Failed to update settings: {result.get('data')}")

    return True

# ============================================================================
# TEST SUITE 7: ATTENDANCE
# ============================================================================

def test_attendance():
    """Test attendance endpoints"""
    print_section("ATTENDANCE API TESTS")

    tenant_slug = test_data.get("tenants", {}).get("test_slug", "acme")

    # First, login as employee
    print_test("0. Login as employee")
    emp_email = test_data["users"]["employee"]["email"]
    result = api_request("POST", "/auth/login/",
                        data={
                            "email": emp_email,
                            "password": "Employee123!"
                        },
                        tenant_id=tenant_slug)
    if result["success"]:
        test_data["tokens"]["employee"] = result["data"]["access"]
        print_success("Employee login successful")
    else:
        print_error(f"Employee login failed: {result.get('data')}")
        return False

    # 7.1 Get attendance settings
    print_test("1. Get attendance settings")
    result = api_request("GET", "/attendance/settings/",
                        token=test_data["tokens"]["employee"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success(f"Attendance settings: work starts at {result['data'].get('work_start_time', 'N/A')}")
    else:
        print_error(f"Failed to get settings: {result.get('data')}")

    # 7.2 Check in
    print_test("2. Check in for attendance")
    result = api_request("POST", "/attendance/checkin/",
                        token=test_data["tokens"]["employee"],
                        tenant_id=tenant_slug,
                        data={
                            "location": {
                                "latitude": 40.7128,
                                "longitude": -74.0060
                            },
                            "notes": "Checked in from office"
                        })
    if result["success"]:
        test_data["attendance"]["checkin"] = result["data"]
        print_success(f"Checked in at: {result['data']['checkin_time']}")
    else:
        print_error(f"Failed to check in: {result.get('data')}")

    # 7.3 Get my attendance
    print_test("3. Get my attendance records")
    result = api_request("GET", "/attendance/my-attendance/",
                        token=test_data["tokens"]["employee"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success(f"Found {len(result['data'])} attendance records")
    else:
        print_error(f"Failed to get attendance: {result.get('data')}")

    # 7.4 Get monthly stats
    print_test("4. Get monthly attendance statistics")
    result = api_request("GET", "/attendance/my-monthly-stats/",
                        token=test_data["tokens"]["employee"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success(f"Monthly stats: {result['data'].get('present_days', 0)} present days")
    else:
        print_error(f"Failed to get stats: {result.get('data')}")

    # 7.5 Check out
    print_test("5. Check out from attendance")
    result = api_request("POST", "/attendance/checkout/",
                        token=test_data["tokens"]["employee"],
                        tenant_id=tenant_slug,
                        data={
                            "location": {
                                "latitude": 40.7128,
                                "longitude": -74.0060
                            },
                            "notes": "Checked out from office"
                        })
    if result["success"]:
        test_data["attendance"]["checkout"] = result["data"]
        print_success(f"Checked out at: {result['data']['checkout_time']}")
        print_success(f"Hours worked: {result['data'].get('hours_worked', 'N/A')}")
    else:
        print_error(f"Failed to check out: {result.get('data')}")

    # 7.6 List all attendance (as admin)
    print_test("6. List all attendance (admin view)")
    result = api_request("GET", "/attendance/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success(f"Found {len(result['data'])} attendance records")
    else:
        print_error(f"Failed to list attendance: {result.get('data')}")

    # 7.7 Update attendance settings (admin only)
    print_test("7. Update attendance settings (admin)")
    result = api_request("PUT", "/attendance/settings/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug,
                        data={
                            "work_start_time": "09:00",
                            "work_end_time": "18:00",
                            "grace_period_minutes": 15,
                            "break_duration_minutes": 60,
                            "overtime_enabled": True,
                            "overtime_start_after_minutes": 480
                        })
    if result["success"]:
        print_success(f"Settings updated: work {result['data']['work_start_time']} - {result['data']['work_end_time']}")
    else:
        print_error(f"Failed to update settings: {result.get('data')}")

    return True

# ============================================================================
# TEST SUITE 8: AUDIT LOGS
# ============================================================================

def test_audit_logs():
    """Test audit log endpoints"""
    print_section("AUDIT LOG API TESTS")

    tenant_slug = test_data.get("tenants", {}).get("test_slug", "acme")

    # 8.1 List audit logs
    print_test("1. List audit logs")
    result = api_request("GET", "/audit/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success(f"Found {len(result['data'])} audit log entries")
        if result["data"]:
            test_data["audit"]["first_id"] = result["data"][0]["id"]
    else:
        print_error(f"Failed to list audit logs: {result.get('data')}")

    # 8.2 Filter audit logs by action
    print_test("2. Filter audit logs by action")
    result = api_request("GET", "/audit/?action=login",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success(f"Found {len(result['data'])} login audit entries")
    else:
        print_error(f"Failed to filter audit logs: {result.get('data')}")

    # 8.3 Get audit log details
    if test_data.get("audit", {}).get("first_id"):
        print_test("3. Get audit log details")
        log_id = test_data["audit"]["first_id"]
        result = api_request("GET", f"/audit/{log_id}/",
                            token=test_data["tokens"]["tenant_admin"],
                            tenant_id=tenant_slug)
        if result["success"]:
            print_success(f"Audit log: {result['data']['action']}")
        else:
            print_error(f"Failed to get audit log details: {result.get('data')}")

    # 8.4 Test audit log access denied for non-admin
    print_test("4. Test audit log access denied for employee")
    result = api_request("GET", "/audit/",
                        token=test_data["tokens"]["employee"],
                        tenant_id=tenant_slug)
    if not result["success"]:
        print_success("Access denied for employee (expected)")
    else:
        print_error("Employee accessed audit logs (should be denied)")

    return True

# ============================================================================
# TEST SUITE 9: MULTI-TENANT ISOLATION
# ============================================================================

def test_multi_tenant_isolation():
    """Test multi-tenant data isolation"""
    print_section("MULTI-TENANT ISOLATION TESTS")

    # 9.1 Create another tenant
    print_test("1. Create second tenant for isolation test")
    tenant2_slug = f"testcompany2-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    result = api_request("POST", "/admin/create-tenant/",
                        token=test_data["tokens"]["superuser"],
                        data={
                            "name": f"Test Company 2 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                            "slug": tenant2_slug,
                            "admin_email": f"admin@{tenant2_slug}.com",
                            "admin_password": "TestAdmin123!",
                            "admin_first_name": "Second",
                            "admin_last_name": "Admin"
                        })
    if result["success"]:
        test_data["tenants"]["test2"] = result["data"]
        test_data["tenants"]["test2_slug"] = tenant2_slug
        print_success(f"Second tenant created: {result['data']['name']}")
    else:
        print_error(f"Failed to create second tenant: {result.get('data')}")
        return False

    # 9.2 Login as second tenant admin
    print_test("2. Login as second tenant admin")
    result = api_request("POST", "/auth/login/",
                        data={
                            "email": f"admin@{tenant2_slug}.com",
                            "password": "TestAdmin123!"
                        },
                        tenant_id=tenant2_slug)
    if result["success"]:
        test_data["tokens"]["tenant2_admin"] = result["data"]["access"]
        print_success("Second tenant admin login successful")
    else:
        print_error(f"Second tenant login failed: {result.get('data')}")
        return False

    # 9.3 Verify tenants can't see each other's users
    print_test("3. Verify tenant isolation - user lists")
    result1 = api_request("GET", "/users/",
                         token=test_data["tokens"]["tenant_admin"],
                         tenant_id=test_data["tenants"]["test_slug"])
    result2 = api_request("GET", "/users/",
                         token=test_data["tokens"]["tenant2_admin"],
                         tenant_id=tenant2_slug)
    if result1["success"] and result2["success"]:
        users1 = [u["email"] for u in result1["data"]]
        users2 = [u["email"] for u in result2["data"]]
        if not any(u in users2 for u in users1):
            print_success("Tenant isolation verified - users are separate")
        else:
            print_error("Tenant isolation failed - users visible across tenants")
    else:
        print_error("Failed to verify user isolation")

    # 9.4 Test subdomain routing (via X-Tenant-ID header)
    print_test("4. Test subdomain routing via header")
    result = api_request("GET", "/users/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant2_slug)  # Try with wrong tenant
    # Should either work with correct tenant context or fail
    print_info(f"Cross-tenant access result: {result.get('data', 'N/A')}")

    return True

# ============================================================================
# TEST SUITE 10: ROLE-BASED ACCESS CONTROL
# ============================================================================

def test_role_based_access_control():
    """Test role-based access control"""
    print_section("ROLE-BASED ACCESS CONTROL TESTS")

    tenant_slug = test_data.get("tenants", {}).get("test_slug", "acme")

    # 10.1 Test Employee cannot access admin endpoints
    print_test("1. Test Employee cannot update org settings")
    result = api_request("PUT", "/organization/settings/",
                        token=test_data["tokens"]["employee"],
                        tenant_id=tenant_slug,
                        data={"timezone": "UTC"})
    if not result["success"]:
        print_success("Access denied for employee (expected)")
    else:
        print_error("Employee updated org settings (should be denied)")

    # 10.2 Test Employee cannot create users
    print_test("2. Test Employee cannot create users")
    result = api_request("POST", "/users/",
                        token=test_data["tokens"]["employee"],
                        tenant_id=tenant_slug,
                        data={
                            "email": "should@fail.com",
                            "first_name": "Should",
                            "last_name": "Fail",
                            "password": "Fail123!"
                        })
    if not result["success"]:
        print_success("Access denied for employee (expected)")
    else:
        print_error("Employee created user (should be denied)")

    # 10.3 Test HR can manage users
    print_test("3. Test HR can list users")
    # Login as HR user
    hr_email = test_data["users"]["hr_user"]["email"]
    result = api_request("POST", "/auth/login/",
                        data={
                            "email": hr_email,
                            "password": "HrUser123!"
                        },
                        tenant_id=tenant_slug)
    if result["success"]:
        test_data["tokens"]["hr_user"] = result["data"]["access"]
        print_success("HR login successful")

        # Try to list users
        result = api_request("GET", "/users/",
                            token=test_data["tokens"]["hr_user"],
                            tenant_id=tenant_slug)
        if result["success"]:
            print_success("HR can list users")
        else:
            print_error("HR cannot list users (unexpected)")
    else:
        print_error(f"HR login failed: {result.get('data')}")

    return True

# ============================================================================
# TEST SUITE 11: ERROR HANDLING
# ============================================================================

def test_error_handling():
    """Test error handling and edge cases"""
    print_section("ERROR HANDLING & EDGE CASES TESTS")

    tenant_slug = test_data.get("tenants", {}).get("test_slug", "acme")

    # 11.1 Test invalid credentials
    print_test("1. Test login with invalid credentials")
    result = api_request("POST", "/auth/login/",
                        data={
                            "email": "invalid@test.com",
                            "password": "WrongPassword123!"
                        })
    if not result["success"]:
        print_success("Login failed as expected")
    else:
        print_error("Invalid credentials accepted (should fail)")

    # 11.2 Test duplicate email
    print_test("2. Test duplicate email registration")
    result = api_request("POST", "/users/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug,
                        data={
                            "email": test_data["users"]["employee"]["email"],
                            "first_name": "Duplicate",
                            "last_name": "Test",
                            "password": "Test123!"
                        })
    if not result["success"]:
        print_success("Duplicate email rejected")
    else:
        print_error("Duplicate email accepted (should fail)")

    # 11.3 Test invalid token
    print_test("3. Test invalid JWT token")
    result = api_request("GET", "/users/me/",
                        token="invalid.token.here",
                        tenant_id=tenant_slug)
    if not result["success"]:
        print_success("Invalid token rejected")
    else:
        print_error("Invalid token accepted (should fail)")

    # 11.4 Test missing required fields
    print_test("4. Test missing required fields")
    result = api_request("POST", "/users/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug,
                        data={
                            "first_name": "Missing Email"
                        })
    if not result["success"]:
        print_success("Missing fields validation works")
    else:
        print_error("Missing fields accepted (should fail)")

    # 11.5 Test invalid date for attendance
    print_test("5. Test checkout without checkin")
    result = api_request("POST", "/attendance/checkout/",
                        token=test_data["tokens"]["employee"],
                        tenant_id=tenant_slug,
                        data={"notes": "No checkin"})
    if not result["success"]:
        print_success("Checkout without checkin rejected")
    else:
        print_error("Checkout without checkin accepted (should fail)")

    # 11.6 Test soft delete user
    print_test("6. Test soft delete user")
    # Create a temporary user
    result = api_request("POST", "/users/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug,
                        data={
                            "email": f"temp.{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com",
                            "first_name": "Temp",
                            "last_name": "User",
                            "password": "Temp123!"
                        })
    if result["success"]:
        temp_user_id = result["data"]["id"]
        # Delete the user
        result = api_request("DELETE", f"/users/{temp_user_id}/",
                            token=test_data["tokens"]["tenant_admin"],
                            tenant_id=tenant_slug)
        if result["success"]:
            print_success("User soft deleted successfully")
        else:
            print_error(f"Failed to delete user: {result.get('data')}")

    return True

# ============================================================================
# TEST SUITE 12: DATA INTEGRITY
# ============================================================================

def test_data_integrity():
    """Test data integrity and relationships"""
    print_section("DATA INTEGRITY TESTS")

    tenant_slug = test_data.get("tenants", {}).get("test_slug", "acme")

    # 12.1 Verify user-role relationship
    print_test("1. Verify user-role relationships")
    result = api_request("GET", "/users/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"]:
        for user in result["data"]:
            if "roles" in user or "role_names" in user:
                print_success(f"User {user['email']} has roles")
                break
    else:
        print_error("Failed to verify user-role relationships")

    # 12.2 Verify cascade deletes (or lack thereof)
    print_test("2. Verify data persistence after role deletion")
    # Roles are soft-delete protected, user should still exist
    result = api_request("GET", f"/users/{test_data['users']['hr_user']['id']}/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"]:
        print_success("User data persists independently")
    else:
        print_error("User data affected by role operations")

    # 12.3 Verify attendance records linked to users
    print_test("3. Verify attendance-user linkage")
    result = api_request("GET", "/attendance/",
                        token=test_data["tokens"]["tenant_admin"],
                        tenant_id=tenant_slug)
    if result["success"] and result["data"]:
        attendance = result["data"][0]
        if "user" in attendance or "user_id" in attendance or "user_email" in attendance:
            print_success("Attendance properly linked to users")
        else:
            print_error("Attendance-user linkage missing")

    return True

# ============================================================================
# SUMMARY REPORT
# ============================================================================

def print_summary():
    """Print test summary"""
    print_section("TEST SUMMARY")
    print(f"{Colors.GREEN}All API tests completed!{Colors.RESET}\n")
    print("Test Coverage:")
    print("  ✓ Authentication (login, logout, token refresh, password management)")
    print("  ✓ Platform Admin (tenant management)")
    print("  ✓ User Management (CRUD operations)")
    print("  ✓ Role Management (assign, revoke, custom roles)")
    print("  ✓ Invitations (create, accept, cancel, resend)")
    print("  ✓ Organization Settings (overview, settings)")
    print("  ✓ Attendance (check-in, check-out, stats, settings)")
    print("  ✓ Audit Logs (logging, filtering)")
    print("  ✓ Multi-Tenant Isolation (data separation)")
    print("  ✓ Role-Based Access Control (permissions)")
    print("  ✓ Error Handling (validation, edge cases)")
    print("  ✓ Data Integrity (relationships, persistence)")

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all API tests"""
    print(f"\n{Colors.BOLD}HRM SAAS API COMPREHENSIVE TEST SUITE{Colors.RESET}")
    print(f"{Colors.BLUE}Testing at: {BASE_URL}{Colors.RESET}\n")

    tests = [
        ("Authentication", test_authentication),
        ("Platform Admin", test_platform_admin),
        ("Tenant Login & Users", test_tenant_login_and_users),
        ("Role Management", test_role_management),
        ("Invitations", test_invitations),
        ("Organization Settings", test_organization_settings),
        ("Attendance", test_attendance),
        ("Audit Logs", test_audit_logs),
        ("Multi-Tenant Isolation", test_multi_tenant_isolation),
        ("Role-Based Access Control", test_role_based_access_control),
        ("Error Handling", test_error_handling),
        ("Data Integrity", test_data_integrity),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print_error(f"{name} tests failed")
        except Exception as e:
            failed += 1
            print_error(f"{name} tests errored: {str(e)}")

    print_summary()
    print(f"\n{Colors.BOLD}Results: {Colors.GREEN}{passed} passed{Colors.RESET}, {Colors.RED}{failed} failed{Colors.RESET}\n")

if __name__ == "__main__":
    main()
