"""
Seed script to create test users for all roles/profiles.

Usage:
    cd backend
    uv run python -m app.seed_test_data

Creates:
- 2 Tenants (Publisher Corp, School District)
- 6 Users (one per role: Admin, Supervisor, Publisher, School, Teacher, Student)

All test users have password: "testpass123"
"""

import logging

from sqlmodel import Session, select

from app.core.db import engine
from app.core.security import get_password_hash
from app.models import Tenant, TenantType, User, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test password for all users
TEST_PASSWORD = "testpass123"

# Test data
TEST_TENANTS = [
    {"name": "Publisher Corp", "tenant_type": TenantType.PUBLISHER},
    {"name": "School District", "tenant_type": TenantType.SCHOOL},
]

TEST_USERS = [
    # Admin - no tenant (can access all)
    {
        "email": "admin@test.com",
        "full_name": "Admin User",
        "role": UserRole.ADMIN,
        "is_superuser": True,
        "tenant_name": None,  # Admin has no tenant
    },
    # Supervisor - no tenant (can access all)
    {
        "email": "supervisor@test.com",
        "full_name": "Supervisor User",
        "role": UserRole.SUPERVISOR,
        "is_superuser": False,
        "tenant_name": None,  # Supervisor has no tenant
    },
    # Publisher - belongs to Publisher Corp tenant
    {
        "email": "publisher@test.com",
        "full_name": "Publisher User",
        "role": UserRole.PUBLISHER,
        "is_superuser": False,
        "tenant_name": "Publisher Corp",
    },
    # School - belongs to School District tenant
    {
        "email": "school@test.com",
        "full_name": "School Admin User",
        "role": UserRole.SCHOOL,
        "is_superuser": False,
        "tenant_name": "School District",
    },
    # Teacher - belongs to School District tenant
    {
        "email": "teacher@test.com",
        "full_name": "Teacher User",
        "role": UserRole.TEACHER,
        "is_superuser": False,
        "tenant_name": "School District",
    },
    # Student - belongs to School District tenant
    {
        "email": "student@test.com",
        "full_name": "Student User",
        "role": UserRole.STUDENT,
        "is_superuser": False,
        "tenant_name": "School District",
    },
]


def create_tenants(session: Session) -> dict[str, Tenant]:
    """Create test tenants if they don't exist."""
    tenants = {}

    for tenant_data in TEST_TENANTS:
        # Check if tenant exists
        existing = session.exec(
            select(Tenant).where(Tenant.name == tenant_data["name"])
        ).first()

        if existing:
            logger.info(f"Tenant already exists: {tenant_data['name']}")
            tenants[tenant_data["name"]] = existing
        else:
            tenant = Tenant(
                name=tenant_data["name"],
                tenant_type=tenant_data["tenant_type"],
            )
            session.add(tenant)
            session.commit()
            session.refresh(tenant)
            logger.info(f"Created tenant: {tenant_data['name']} (ID: {tenant.id})")
            tenants[tenant_data["name"]] = tenant

    return tenants


def create_users(session: Session, tenants: dict[str, Tenant]) -> list[User]:
    """Create test users if they don't exist."""
    users = []

    for user_data in TEST_USERS:
        # Check if user exists
        existing = session.exec(
            select(User).where(User.email == user_data["email"])
        ).first()

        if existing:
            logger.info(f"User already exists: {user_data['email']}")
            users.append(existing)
            continue

        # Get tenant_id
        tenant_id = None
        tenant_name = (
            str(user_data["tenant_name"]) if user_data["tenant_name"] else None
        )
        if tenant_name:
            tenant = tenants.get(tenant_name)
            if tenant:
                tenant_id = tenant.id

        # Create user
        user = User(
            email=user_data["email"],
            full_name=user_data["full_name"],
            hashed_password=get_password_hash(TEST_PASSWORD),
            role=user_data["role"],
            is_superuser=user_data["is_superuser"],
            is_active=True,
            tenant_id=tenant_id,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        role = user_data["role"]
        role_value = role.value if hasattr(role, "value") else str(role)
        logger.info(
            f"Created user: {user_data['email']} "
            f"(Role: {role_value}, Tenant: {user_data['tenant_name'] or 'None'})"
        )
        users.append(user)

    return users


def main() -> None:
    """Main function to seed test data."""
    logger.info("=" * 60)
    logger.info("SEEDING TEST DATA")
    logger.info("=" * 60)

    with Session(engine) as session:
        # Create tenants
        logger.info("\n--- Creating Tenants ---")
        tenants = create_tenants(session)

        # Create users
        logger.info("\n--- Creating Users ---")
        _users = create_users(session, tenants)  # noqa: F841

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST DATA SUMMARY")
    logger.info("=" * 60)
    logger.info(f"\nPassword for all test users: {TEST_PASSWORD}")
    logger.info("\nTest Users:")
    logger.info("-" * 60)
    logger.info(f"{'Email':<30} {'Role':<15} {'Tenant':<20}")
    logger.info("-" * 60)

    for user_data in TEST_USERS:
        role = user_data["role"]
        role_value = role.value if hasattr(role, "value") else str(role)
        logger.info(
            f"{user_data['email']:<30} "
            f"{role_value:<15} "
            f"{user_data['tenant_name'] or 'N/A':<20}"
        )

    logger.info("-" * 60)
    logger.info("\nTo login, use POST /api/v1/login/access-token with:")
    logger.info("  username: <email>")
    logger.info("  password: testpass123")
    logger.info("\nExample curl:")
    logger.info(
        '  curl -X POST "http://localhost:8000/api/v1/login/access-token" '
        '-d "username=admin@test.com&password=testpass123"'
    )


if __name__ == "__main__":
    main()
