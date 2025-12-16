#!/usr/bin/env python3
# ruff: noqa: T201 - print statements are intentional for CLI output
"""
Rate Limiting Test Script (Story 2.4)

Tests the rate limiting functionality for different user roles.

Usage:
    # Test with default settings (requires running backend)
    uv run python scripts/test_rate_limiting.py

    # Test with custom base URL
    uv run python scripts/test_rate_limiting.py --base-url http://localhost:8000

    # Test specific role
    uv run python scripts/test_rate_limiting.py --role student

    # Quick test (fewer requests)
    uv run python scripts/test_rate_limiting.py --quick

Environment Variables:
    TEST_USER_EMAIL: Email for test user (default: student@example.com)
    TEST_USER_PASSWORD: Password for test user (default: changethis)
"""

import argparse
import sys
import time
from dataclasses import dataclass

import httpx

# Default configuration
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_API_PREFIX = "/api/v1"
DEFAULT_PASSWORD = "testpass123"

# Test users (created by scripts/create_test_users.py)
TEST_USERS = {
    "admin": {"email": "admin@test.com", "password": DEFAULT_PASSWORD},
    "supervisor": {"email": "supervisor@test.com", "password": DEFAULT_PASSWORD},
    "publisher": {"email": "publisher@test.com", "password": DEFAULT_PASSWORD},
    "school": {"email": "school@test.com", "password": DEFAULT_PASSWORD},
    "teacher": {"email": "teacher@test.com", "password": DEFAULT_PASSWORD},
    "student": {"email": "student@test.com", "password": DEFAULT_PASSWORD},
}

# Expected rate limits per role
EXPECTED_LIMITS = {
    "admin": None,  # Unlimited
    "supervisor": None,  # Unlimited
    "publisher": 1000,  # per hour
    "school": 1000,  # per hour
    "teacher": 500,  # per hour
    "student": 100,  # per hour
}


@dataclass
class RateLimitTestResult:
    """Result of a rate limit test."""

    role: str
    requests_made: int
    requests_succeeded: int
    requests_rate_limited: int
    first_rate_limit_at: int | None
    retry_after: int | None
    error_response: dict | None


def get_access_token(
    client: httpx.Client, base_url: str, email: str, password: str
) -> str | None:
    """Get access token for a user."""
    try:
        response = client.post(
            f"{base_url}{DEFAULT_API_PREFIX}/auth/login",
            data={"username": email, "password": password},
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        print(f"  Login failed: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        print(f"  Login error: {e}")
        return None


def test_rate_limit(
    client: httpx.Client,
    base_url: str,
    token: str | None,
    endpoint: str,
    num_requests: int,
    delay_ms: int = 10,
) -> RateLimitTestResult:
    """Test rate limiting by making multiple requests."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    succeeded = 0
    rate_limited = 0
    first_rate_limit_at = None
    retry_after = None
    error_response = None

    for i in range(num_requests):
        try:
            response = client.get(
                f"{base_url}{DEFAULT_API_PREFIX}{endpoint}",
                headers=headers,
            )

            if response.status_code == 200:
                succeeded += 1
            elif response.status_code == 429:
                rate_limited += 1
                if first_rate_limit_at is None:
                    first_rate_limit_at = i + 1
                    retry_after = response.headers.get("Retry-After")
                    error_response = response.json()
            else:
                print(f"    Unexpected status: {response.status_code}")

            # Small delay to avoid overwhelming the server
            if delay_ms > 0:
                time.sleep(delay_ms / 1000)

        except Exception as e:
            print(f"    Request error: {e}")

    return RateLimitTestResult(
        role="unknown",
        requests_made=num_requests,
        requests_succeeded=succeeded,
        requests_rate_limited=rate_limited,
        first_rate_limit_at=first_rate_limit_at,
        retry_after=int(retry_after) if retry_after else None,
        error_response=error_response,
    )


def print_result(result: RateLimitTestResult) -> None:
    """Print test result."""
    print(f"\n  Results for {result.role}:")
    print(f"    Requests made: {result.requests_made}")
    print(f"    Succeeded: {result.requests_succeeded}")
    print(f"    Rate limited (429): {result.requests_rate_limited}")

    if result.first_rate_limit_at:
        print(f"    First rate limit at request #{result.first_rate_limit_at}")
        print(f"    Retry-After header: {result.retry_after} seconds")
        if result.error_response:
            print(f"    Error code: {result.error_response.get('error_code')}")
            print(f"    Message: {result.error_response.get('message')}")
    else:
        print("    No rate limiting triggered")


def test_role(
    client: httpx.Client,
    base_url: str,
    role: str,
    num_requests: int,
    quick: bool = False,
) -> RateLimitTestResult | None:
    """Test rate limiting for a specific role."""
    print(f"\n{'=' * 60}")
    print(f"Testing {role.upper()} role")
    print(f"{'=' * 60}")

    user = TEST_USERS.get(role)
    if not user:
        print(f"  No test user configured for role: {role}")
        return None

    print(f"  Logging in as {user['email']}...")
    token = get_access_token(client, base_url, user["email"], user["password"])
    if not token:
        print("  Failed to get access token. Skipping role test.")
        return None

    print(f"  Access token obtained. Making {num_requests} requests...")

    # Use /users/me endpoint for testing (always accessible to authenticated users)
    result = test_rate_limit(
        client,
        base_url,
        token,
        "/users/me",
        num_requests,
        delay_ms=5 if quick else 10,
    )
    result.role = role

    print_result(result)
    return result


def test_unauthenticated(
    client: httpx.Client, base_url: str, num_requests: int
) -> RateLimitTestResult:
    """Test rate limiting for unauthenticated requests."""
    print(f"\n{'=' * 60}")
    print("Testing UNAUTHENTICATED requests")
    print(f"{'=' * 60}")

    print(f"  Making {num_requests} requests without authentication...")

    # Use health check which doesn't require auth but still goes through rate limiting
    # Actually, health check is excluded from rate limiting
    # Let's try a public endpoint or just show the behavior
    result = test_rate_limit(
        client,
        base_url,
        None,
        "/utils/health-check",  # This might not have rate limiting
        num_requests,
        delay_ms=10,
    )
    result.role = "unauthenticated"

    print_result(result)
    return result


def test_login_rate_limit(
    client: httpx.Client, base_url: str, num_requests: int = 10
) -> None:
    """Test login endpoint rate limiting (IP-based)."""
    print(f"\n{'=' * 60}")
    print("Testing LOGIN rate limiting (IP-based)")
    print(f"{'=' * 60}")

    print(f"  Making {num_requests} login attempts...")

    succeeded = 0
    rate_limited = 0
    first_rate_limit_at = None

    for i in range(num_requests):
        try:
            response = client.post(
                f"{base_url}{DEFAULT_API_PREFIX}/auth/login",
                data={"username": "test@example.com", "password": "wrongpassword"},
            )

            if response.status_code == 401:  # Invalid credentials (expected)
                succeeded += 1
            elif response.status_code == 429:
                rate_limited += 1
                if first_rate_limit_at is None:
                    first_rate_limit_at = i + 1
                    print(f"    Rate limited at request #{i + 1}")
                    print(f"    Retry-After: {response.headers.get('Retry-After')}")

            time.sleep(0.1)  # 100ms between requests

        except Exception as e:
            print(f"    Request error: {e}")

    print("\n  Results:")
    print(f"    Requests made: {num_requests}")
    print(f"    Processed (401): {succeeded}")
    print(f"    Rate limited (429): {rate_limited}")
    if first_rate_limit_at:
        print(f"    First rate limit at request #{first_rate_limit_at}")


def show_current_limits() -> None:
    """Show current rate limit configuration."""
    print("\n" + "=" * 60)
    print("Current Rate Limit Configuration")
    print("=" * 60)
    print("\nExpected limits (from architecture):")
    for role, limit in EXPECTED_LIMITS.items():
        if limit is None:
            print(f"  {role:12s}: Unlimited")
        else:
            print(f"  {role:12s}: {limit}/hour")

    print("\nEnvironment variable overrides:")
    print("  RATE_LIMIT_PUBLISHER  - Publisher limit (default: 1000/hour)")
    print("  RATE_LIMIT_SCHOOL     - School limit (default: 1000/hour)")
    print("  RATE_LIMIT_TEACHER    - Teacher limit (default: 500/hour)")
    print("  RATE_LIMIT_STUDENT    - Student limit (default: 100/hour)")
    print("  RATE_LIMIT_DEFAULT    - Unauthenticated limit (default: 100/hour)")
    print("  RATE_LIMIT_LOGIN      - Login attempts (default: 5/minute)")
    print("  RATE_LIMIT_SIGNUP     - Signup attempts (default: 10/minute)")


def main() -> int:
    """Run rate limiting tests."""
    parser = argparse.ArgumentParser(
        description="Test rate limiting functionality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Base URL for the API (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--role",
        choices=[
            "admin",
            "supervisor",
            "publisher",
            "school",
            "teacher",
            "student",
            "all",
        ],
        default="all",
        help="Role to test (default: all)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick test with fewer requests",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=None,
        help="Number of requests to make (default: varies by test mode)",
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Show rate limit configuration and exit",
    )
    parser.add_argument(
        "--test-login",
        action="store_true",
        help="Test login rate limiting",
    )

    args = parser.parse_args()

    if args.show_config:
        show_current_limits()
        return 0

    # Determine number of requests
    if args.requests:
        num_requests = args.requests
    elif args.quick:
        num_requests = 20
    else:
        num_requests = 110  # Enough to trigger student limit (100/hour)

    print("=" * 60)
    print("Rate Limiting Test Script")
    print("=" * 60)
    print(f"\nBase URL: {args.base_url}")
    print(f"Requests per test: {num_requests}")
    print(f"Mode: {'Quick' if args.quick else 'Full'}")

    # Check if server is reachable
    with httpx.Client(timeout=10.0) as client:
        try:
            response = client.get(
                f"{args.base_url}{DEFAULT_API_PREFIX}/utils/health-check"
            )
            if response.status_code != 200:
                print(f"\nWarning: Health check returned {response.status_code}")
        except httpx.ConnectError:
            print(f"\nError: Cannot connect to {args.base_url}")
            print("Make sure the backend server is running.")
            return 1

        # Test login rate limiting if requested
        if args.test_login:
            test_login_rate_limit(client, args.base_url, min(num_requests, 10))

        # Test roles
        roles_to_test = (
            ["admin", "supervisor", "publisher", "school", "teacher", "student"]
            if args.role == "all"
            else [args.role]
        )

        results = []
        for role in roles_to_test:
            result = test_role(client, args.base_url, role, num_requests, args.quick)
            if result:
                results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for result in results:
        expected = EXPECTED_LIMITS.get(result.role)
        status = ""
        if expected is None:
            status = "PASS" if result.requests_rate_limited == 0 else "UNEXPECTED"
        elif result.first_rate_limit_at:
            if result.first_rate_limit_at <= expected + 10:  # Allow some margin
                status = "PASS"
            else:
                status = f"LATE (expected ~{expected})"
        else:
            status = f"NOT HIT (expected at ~{expected})"

        print(
            f"  {result.role:12s}: {result.requests_succeeded} OK, "
            f"{result.requests_rate_limited} limited - {status}"
        )

    print("\nNote: Rate limits are per hour. To fully test limits,")
    print("you may need to wait for the time window to reset.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
