from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import Participant, ScreeningPeriod, ScreeningAuditLog

STATUSES = ("Pending", "Lolos", "Tidak Lolos")

class ScreeningError(Exception):
    pass

def active_period():
    return ScreeningPeriod.query.filter_by(is_active=True).first()

def create_participant(data, mentor_user_id, period):
    participant = Participant(name=data["name"].strip(), nim=data["nim"].strip(), class_name=data["class_name"].strip(), organization_experience=data["organization_experience"].strip(), achievements=data["achievements"].strip(), mentor_id=mentor_user_id, period_id=period.id)
    db.session.add(participant)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ScreeningError("NIM ini sudah pernah melakukan screening pada periode aktif.")
    return participant

def review_participant(participant, actor, status, note):
    if status not in STATUSES:
        raise ScreeningError("Status screening tidak valid.")
    old = participant.status
    participant.status = status
    participant.mentor_note = note.strip()
    participant.reviewed_at = datetime.now(timezone.utc)
    db.session.add(ScreeningAuditLog(participant_id=participant.id, actor_id=actor.id, previous_status=old, new_status=status, note=note.strip()))
    db.session.commit()
