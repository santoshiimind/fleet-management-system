"""
Alerts API routes — View, acknowledge, and manage fleet alerts.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta

from models.database import get_db
from models.alert import Alert, AlertType, AlertSeverity

router = APIRouter(prefix="/alerts", tags=["Alerts"])


class AlertResponse(BaseModel):
    id: int
    vehicle_id: int
    alert_type: str
    severity: str
    message: str
    details: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    trigger_value: Optional[float]
    threshold_value: Optional[float]
    is_acknowledged: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[AlertResponse])
def list_alerts(
    vehicle_id: Optional[int] = None,
    severity: Optional[AlertSeverity] = None,
    alert_type: Optional[AlertType] = None,
    acknowledged: Optional[bool] = None,
    hours: int = Query(24, ge=1, le=720),
    skip: int = 0,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List alerts with optional filters."""
    since = datetime.utcnow() - timedelta(hours=hours)
    query = db.query(Alert).filter(Alert.created_at >= since)

    if vehicle_id:
        query = query.filter(Alert.vehicle_id == vehicle_id)
    if severity:
        query = query.filter(Alert.severity == severity)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if acknowledged is not None:
        query = query.filter(Alert.is_acknowledged == acknowledged)

    return query.order_by(desc(Alert.created_at)).offset(skip).limit(limit).all()


@router.put("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, acknowledged_by: str = "admin", db: Session = Depends(get_db)):
    """Acknowledge an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "Alert not found")

    alert.is_acknowledged = True
    alert.acknowledged_by = acknowledged_by
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    return {"message": "Alert acknowledged", "alert_id": alert_id}


@router.get("/summary")
def alert_summary(hours: int = Query(24, ge=1, le=720), db: Session = Depends(get_db)):
    """Get alert count summary by type and severity."""
    since = datetime.utcnow() - timedelta(hours=hours)
    alerts = db.query(Alert).filter(Alert.created_at >= since).all()

    by_severity = {"info": 0, "warning": 0, "critical": 0}
    by_type = {}
    unacknowledged = 0

    for a in alerts:
        by_severity[a.severity.value] = by_severity.get(a.severity.value, 0) + 1
        by_type[a.alert_type.value] = by_type.get(a.alert_type.value, 0) + 1
        if not a.is_acknowledged:
            unacknowledged += 1

    return {
        "total": len(alerts),
        "unacknowledged": unacknowledged,
        "by_severity": by_severity,
        "by_type": by_type,
        "period_hours": hours,
    }
