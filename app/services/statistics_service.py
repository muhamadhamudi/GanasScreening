from sqlalchemy import func
from app.models import Participant, User

def counts(query):
    return {"total": query.count(), "pending": query.filter_by(status="Pending").count(), "passed": query.filter_by(status="Lolos").count(), "failed": query.filter_by(status="Tidak Lolos").count()}

def mentor_summary():
    rows=[]
    for user in User.query.filter_by(role="mentor").order_by(User.display_name).all():
        c=counts(Participant.query.filter_by(mentor_id=user.id))
        rows.append({"mentor":user,"counts":c})
    return rows
