import pytest
from app import create_app
from app.extensions import db
from app.models import User, Mentor, ScreeningPeriod
from app.services.qr_service import new_token

@pytest.fixture
def app(tmp_path):
    class TestConfig:
        TESTING=True
        SECRET_KEY="test-secret-key"
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path/'test.db'}"
        SQLALCHEMY_TRACK_MODIFICATIONS=False
        WTF_CSRF_ENABLED=False
        PUBLIC_BASE_URL="https://test.example"
    application=create_app(TestConfig)
    with application.app_context():
        db.drop_all(); db.create_all()
        admin=User(username="admin",display_name="Admin",role="admin"); admin.set_password("AdminPass123!")
        mentor=User(username="mentor01",display_name="Mentor 01",role="mentor"); mentor.set_password("MentorPass123!"); mentor.mentor_profile=Mentor(qr_token=new_token())
        mentor2=User(username="mentor02",display_name="Mentor 02",role="mentor"); mentor2.set_password("MentorPass123!"); mentor2.mentor_profile=Mentor(qr_token=new_token())
        db.session.add_all([admin,mentor,mentor2]); db.session.add(ScreeningPeriod(name="Test period",is_active=True)); db.session.commit()
        yield application
        db.session.remove(); db.drop_all()

@pytest.fixture
def client(app): return app.test_client()

def login(client, role, username, password):
    path="/admin/login" if role=="admin" else "/mentor/login"
    return client.post(path,data={"username":username,"password":password},follow_redirects=True)
