import asyncio
from database import engine, AsyncSessionLocal
from auth.models import Role, User, AccessLevel
from auth.router import get_password_hash
from sqlalchemy.future import select

async def seed():
    async with AsyncSessionLocal() as db:
        # Create roles
        roles_data = [
            {"name": "admin", "max_access_level": AccessLevel.RESTRICTED, "can_upload": True, "can_manage": True},
            {"name": "manager", "max_access_level": AccessLevel.CONFIDENTIAL, "can_upload": True, "can_manage": False},
            {"name": "employee", "max_access_level": AccessLevel.INTERNAL, "can_upload": False, "can_manage": False},
            {"name": "viewer", "max_access_level": AccessLevel.PUBLIC, "can_upload": False, "can_manage": False},
        ]
        
        roles = {}
        for rd in roles_data:
            res = await db.execute(select(Role).filter(Role.name == rd["name"]))
            existing = res.scalars().first()
            if not existing:
                role = Role(
                    name=rd["name"],
                    max_access_level=rd["max_access_level"],
                    can_upload_docs=rd["can_upload"],
                    can_manage_users=rd["can_manage"]
                )
                db.add(role)
                roles[rd["name"]] = role
            else:
                roles[rd["name"]] = existing
        
        await db.commit()
        
        # Create users
        users_data = [
            {"email": "admin@demo.com", "name": "Admin", "password": "admin123", "role": "admin"},
            {"email": "manager@demo.com", "name": "Manager", "password": "manager123", "role": "manager"},
            {"email": "employee@demo.com", "name": "Employee", "password": "employee123", "role": "employee"},
            {"email": "viewer@demo.com", "name": "Viewer", "password": "viewer123", "role": "viewer"},
        ]
        
        for ud in users_data:
            res = await db.execute(select(User).filter(User.email == ud["email"]))
            if not res.scalars().first():
                role = roles.get(ud["role"])
                user = User(
                    email=ud["email"],
                    name=ud["name"],
                    hashed_password=get_password_hash(ud["password"]),
                    role_id=role.id if role else None,
                    access_level=role.max_access_level if role else AccessLevel.PUBLIC
                )
                db.add(user)
                
        await db.commit()
        print("Database seeded with demo users and roles.")

if __name__ == "__main__":
    asyncio.run(seed())
