#!/usr/bin/env python3
# ruff: noqa: T201 - print statements are intentional for CLI output
"""
Create Test Users Script (Story 2.4)

Creates test users for development and testing rate limiting.

Usage:
    # Create all test users (requires database connection)
    uv run python scripts/create_test_users.py

    # List users that would be created (dry run)
    uv run python scripts/create_test_users.py --dry-run

    # Delete test users
    uv run python scripts/create_test_users.py --delete

Environment:
    Requires DATABASE_URL or individual POSTGRES_* environment variables.
"""

import argparse
import sys
from uuid import UUID, uuid4

from sqlmodel import Session, select

from app.core.db import engine
from app.core.security import get_password_hash
from app.models import Tenant, TenantType, User, UserRole

# Test user configuration
DEFAULT_PASSWORD = "testpass123"

# Tenant configurations
TENANTS = {
    "publisher_corp": {
        "id": UUID("72dd9e54-8e35-4a1b-9c2d-3e4f5a6b7c8d"),
        "name": "Publisher Corp",
        "tenant_type": TenantType.PUBLISHER,
    },
    "school_district": {
        "id": UUID("a95225f0-fc52-4b3e-8d1c-2e3f4a5b6c7d"),
        "name": "School District",
        "tenant_type": TenantType.SCHOOL,
    },
}

# Test user configurations
TEST_USERS = [
    {
        "email": "admin@test.com",
        "role": UserRole.ADMIN,
        "tenant_id": None,
        "full_name": "Test Admin",
        "is_superuser": True,
    },
    {
        "email": "supervisor@test.com",
        "role": UserRole.SUPERVISOR,
        "tenant_id": None,
        "full_name": "Test Supervisor",
        "is_superuser": True,
    },
    {
        "email": "publisher@test.com",
        "role": UserRole.PUBLISHER,
        "tenant_id": TENANTS["publisher_corp"]["id"],
        "full_name": "Test Publisher",
        "is_superuser": False,
    },
    {
        "email": "school@test.com",
        "role": UserRole.SCHOOL,
        "tenant_id": TENANTS["school_district"]["id"],
        "full_name": "Test School",
        "is_superuser": False,
    },
    {
        "email": "teacher@test.com",
        "role": UserRole.TEACHER,
        "tenant_id": TENANTS["school_district"]["id"],
        "full_name": "Test Teacher",
        "is_superuser": False,
    },
    {
        "email": "student@test.com",
        "role": UserRole.STUDENT,
        "tenant_id": TENANTS["school_district"]["id"],
        "full_name": "Test Student",
        "is_superuser": False,
    },
]


def create_tenants(session: Session, dry_run: bool = False) -> dict[UUID, Tenant]:
    """Create test tenants if they don't exist."""
    created_tenants = {}

    for _key, config in TENANTS.items():
        # Check if tenant exists
        existing = session.get(Tenant, config["id"])
        if existing:
            print(f"  Tenant '{config['name']}' already exists")
            created_tenants[config["id"]] = existing
            continue

        if dry_run:
            print(f"  [DRY RUN] Would create tenant: {config['name']}")
            continue

        tenant = Tenant(
            id=config["id"],
            name=config["name"],
            tenant_type=config["tenant_type"],
        )
        session.add(tenant)
        created_tenants[config["id"]] = tenant
        print(f"  Created tenant: {config['name']} ({config['id']})")

    if not dry_run:
        session.commit()

    return created_tenants


def create_users(session: Session, password: str, dry_run: bool = False) -> list[User]:
    """Create test users."""
    created_users = []
    hashed_password = get_password_hash(password)

    for user_config in TEST_USERS:
        # Check if user exists
        statement = select(User).where(User.email == user_config["email"])
        existing = session.exec(statement).first()

        if existing:
            print(
                f"  User '{user_config['email']}' already exists (role: {existing.role})"
            )
            created_users.append(existing)
            continue

        if dry_run:
            print(
                f"  [DRY RUN] Would create: {user_config['email']} "
                f"(role: {user_config['role'].value})"
            )
            continue

        user = User(
            id=uuid4(),
            email=user_config["email"],
            hashed_password=hashed_password,
            full_name=user_config["full_name"],
            role=user_config["role"],
            tenant_id=user_config["tenant_id"],
            is_active=True,
            is_superuser=user_config["is_superuser"],
        )
        session.add(user)
        created_users.append(user)
        print(
            f"  Created: {user_config['email']} "
            f"(role: {user_config['role'].value}, tenant: {user_config['tenant_id']})"
        )

    if not dry_run:
        session.commit()

    return created_users


def delete_users(session: Session, dry_run: bool = False) -> int:
    """Delete test users."""
    deleted_count = 0

    for user_config in TEST_USERS:
        statement = select(User).where(User.email == user_config["email"])
        user = session.exec(statement).first()

        if not user:
            print(f"  User '{user_config['email']}' not found")
            continue

        if dry_run:
            print(f"  [DRY RUN] Would delete: {user_config['email']}")
            deleted_count += 1
            continue

        session.delete(user)
        deleted_count += 1
        print(f"  Deleted: {user_config['email']}")

    if not dry_run:
        session.commit()

    return deleted_count


def show_users_table() -> None:
    """Display the test users table."""
    print("\nTest Users Configuration:")
    print("-" * 80)
    print(f"{'Email':<25} {'Role':<12} {'Tenant':<20} {'Superuser':<10}")
    print("-" * 80)

    for user in TEST_USERS:
        tenant_name = "None (full access)"
        if user["tenant_id"]:
            for _key, config in TENANTS.items():
                if config["id"] == user["tenant_id"]:
                    tenant_name = config["name"]
                    break

        print(
            f"{user['email']:<25} "
            f"{user['role'].value:<12} "
            f"{tenant_name:<20} "
            f"{str(user['is_superuser']):<10}"
        )

    print("-" * 80)
    print(f"\nPassword for all users: {DEFAULT_PASSWORD}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create test users for rate limiting testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without making changes",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete test users instead of creating them",
    )
    parser.add_argument(
        "--password",
        default=DEFAULT_PASSWORD,
        help=f"Password for all test users (default: {DEFAULT_PASSWORD})",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show test users configuration and exit",
    )

    args = parser.parse_args()

    if args.show:
        show_users_table()
        return 0

    print("=" * 60)
    print("Test Users Management Script")
    print("=" * 60)

    if args.dry_run:
        print("\n[DRY RUN MODE - No changes will be made]\n")

    try:
        with Session(engine) as session:
            if args.delete:
                print("\nDeleting test users...")
                deleted = delete_users(session, args.dry_run)
                print(f"\nDeleted {deleted} users")
            else:
                print("\nCreating tenants...")
                create_tenants(session, args.dry_run)

                print("\nCreating test users...")
                users = create_users(session, args.password, args.dry_run)
                print(f"\nProcessed {len(users)} users")

                if not args.dry_run:
                    show_users_table()

    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("  1. The database is running")
        print("  2. Environment variables are set (DATABASE_URL or POSTGRES_*)")
        print("  3. Database migrations have been applied")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
