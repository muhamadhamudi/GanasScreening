from datetime import datetime, timezone
from sqlalchemy import text, Index
from app.extensions import db

class ScreeningPeriod(db.Model):
    __tablename__ = "screening_periods"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default="")
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    participants = db.relationship("Participant", back_populates="period")
    __table_args__ = (Index("uq_single_active_period", "is_active", unique=True, sqlite_where=text("is_active = 1")),)
