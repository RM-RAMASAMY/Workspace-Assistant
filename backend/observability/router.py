from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from auth.dependencies import require_role
from auth.models import AccessLevel, User
from . import models

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(require_role(AccessLevel.RESTRICTED)), db: AsyncSession = Depends(get_db)):
    # Admins only
    result = await db.execute(select(models.QueryLog))
    logs = result.scalars().all()
    
    total_queries = len(logs)
    avg_latency = sum(log.latency_total_ms for log in logs) / total_queries if total_queries > 0 else 0
    
    return {
        "total_queries": total_queries,
        "avg_latency_ms": avg_latency,
        "recent_queries": [{"query": log.query, "timestamp": log.timestamp} for log in logs[-10:]]
    }
