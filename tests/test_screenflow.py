from app.extensions import db
from app.models import User, Mentor, Participant, ScreeningPeriod, ScreeningAuditLog
from tests.conftest import login

def payload(nim="NIM001"):
    return {"name":"Peserta Test","nim":nim,"class_name":"TI-1A","organization_experience":"BEM","achievements":"Juara"}

def test_public_routes_and_health(client):
    assert client.get("/").status_code==200
    assert client.get("/scan").status_code==200
    assert client.get("/health").json["status"]=="ok"

def test_guest_cannot_access_dashboard(client):
    response=client.get("/mentor/dashboard")
    assert response.status_code in (302,401)
    response=client.get("/admin/dashboard")
    assert response.status_code in (302,401)

def test_screening_is_assigned_to_qr_owner(app,client):
    with app.app_context():
        mentor=User.query.filter_by(username="mentor01").first()
        token=mentor.mentor_profile.qr_token
    assert client.get(f"/s/{token}").status_code==200
    response=client.post(f"/s/{token}",data=payload())
    assert response.status_code==200
    with app.app_context():
        p=Participant.query.filter_by(nim="NIM001").one()
        assert p.mentor.username=="mentor01"
        assert p.status=="Pending"

def test_duplicate_nim_is_rejected_across_mentors(app,client):
    with app.app_context():
        mentors=User.query.filter_by(role="mentor").order_by(User.id).all()
        tokens=[m.mentor_profile.qr_token for m in mentors]
    assert client.post(f"/s/{tokens[0]}",data=payload("ABC" )).status_code==200
    assert client.post(f"/s/{tokens[1]}",data=payload("abc")).status_code==409
    with app.app_context(): assert Participant.query.count()==1

def test_mentor_isolation_and_review(app,client):
    with app.app_context(): token=User.query.filter_by(username="mentor01").first().mentor_profile.qr_token
    client.post(f"/s/{token}",data=payload())
    login(client,"mentor","mentor02","MentorPass123!")
    assert client.get("/mentor/participants/1").status_code==404
    client.post("/logout")
    login(client,"mentor","mentor01","MentorPass123!")
    assert client.get("/mentor/participants/1").status_code==200
    response=client.post("/mentor/participants/1/review",data={"status":"Lolos","mentor_note":"Direkomendasikan"},follow_redirects=True)
    assert response.status_code==200
    with app.app_context():
        p=db.session.get(Participant,1)
        assert p.status=="Lolos"
        assert p.mentor_note=="Direkomendasikan"
        assert ScreeningAuditLog.query.filter_by(participant_id=1).count()==1

def test_disabled_mentor_qr_is_invalid(app,client):
    with app.app_context():
        mentor=User.query.filter_by(username="mentor01").first(); token=mentor.mentor_profile.qr_token; mentor.is_active=False; db.session.commit()
    assert client.get(f"/s/{token}").status_code==404

def test_qr_reset_invalidates_old_token(app,client):
    with app.app_context():
        mentor=User.query.filter_by(username="mentor01").first(); old=mentor.mentor_profile.qr_token; mentor_id=mentor.id
    login(client,"admin","admin","AdminPass123!")
    response=client.post(f"/admin/mentors/{mentor_id}/qr/reset",follow_redirects=True)
    assert response.status_code==200
    assert client.get(f"/s/{old}").status_code==404

def test_admin_csv_export(client):
    login(client,"admin","admin","AdminPass123!")
    response=client.get("/admin/export")
    assert response.status_code==200
    assert "text/csv" in response.content_type
