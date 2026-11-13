from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, UniqueConstraint
from app.extensions import db

class Participant(db.Model):
    __tablename__ = "participants"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    nim = db.Column(db.String(50, collation="NOCASE"), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    organization_experience = db.Column(db.Text, nullable=False)
    achievements = db.Column(db.Text, nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    period_id = db.Column(db.Integer, db.ForeignKey("screening_periods.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="Pending", index=True)
    mentor_note = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    mentor = db.relationship("User", back_populates="participants", foreign_keys=[mentor_id])
    period = db.relationship("ScreeningPeriod", back_populates="participants")
    __table_args__ = (UniqueConstraint("period_id", "nim", name="uq_participant_period_nim"), CheckConstraint("status IN ('Pending', 'Lolos', 'Tidak Lolos')", name="ck_participant_status"))
