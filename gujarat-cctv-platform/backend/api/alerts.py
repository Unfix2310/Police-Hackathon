from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from database import get_db
from auth.rbac import require_role
from models.user import User
from models.alert import Alert

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("")
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["operator", "command"]))
):
    """List active unacknowledged alerts."""
    query = (
        select(Alert)
        .where(Alert.status != 'ACKNOWLEDGED')
        .order_by(desc(Alert.created_at))
        .limit(50)
    )
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return [
        {
            "alert_id": a.alert_id,
            "alert_type": a.alert_type,
            "priority": a.priority.value if hasattr(a.priority, "value") else a.priority,
            "message": a.message,
            "created_at": a.created_at,
            "status": a.status,
            "jurisdiction_code": a.jurisdiction_code
        } for a in alerts
    ]

@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["operator", "investigator", "command"]))
):
    """Acknowledge an alert — persists status, actor, timestamp, and comments."""
    from datetime import datetime, timezone
    
    result = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    
    alert.status = "ACKNOWLEDGED"
    # Store acknowledgement metadata in a simple pattern
    ack_comment = payload.get("comment", "")
    ack_actor = user.get("user_id", "unknown")
    ack_time = datetime.now(timezone.utc).isoformat()
    alert.message = f"{alert.message or ''} [ACK by {ack_actor} at {ack_time}] {ack_comment}".strip()
    
    await db.commit()
    
    return {
        "alert_id": alert.alert_id,
        "status": "ACKNOWLEDGED",
        "acknowledged_by": ack_actor,
        "acknowledged_at": ack_time,
        "comment": ack_comment,
    }
