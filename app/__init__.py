import os, secrets
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import event
from dotenv import load_dotenv
from app.extensions import db, login_manager, csrf
from app.models import User, Mentor, ScreeningPeriod
from app.services.qr_service import new_token

load_dotenv()

def create_app(config_object="config.Config"):
    app=Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)
    if os.environ.get("FLASK_ENV") == "production" and (not app.config.get("SECRET_KEY") or app.config.get("SECRET_KEY") == "dev-only-change-me"):
        raise RuntimeError("SECRET_KEY wajib diatur untuk production.")
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app); login_manager.init_app(app); csrf.init_app(app)
    with app.app_context():
        @event.listens_for(db.engine, "connect")
        def enable_sqlite_foreign_keys(connection, record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    login_manager.login_view="auth.admin_login"
    login_manager.login_message="Silakan login untuk melanjutkan."
    login_manager.session_protection="strong"
    @login_manager.unauthorized_handler
    def unauthorized():
        endpoint = "auth.mentor_login" if request.path.startswith("/mentor") else "auth.admin_login"
        return redirect(url_for(endpoint))
    from app.blueprints.public.routes import public_bp
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.admin.routes import admin_bp
    from app.blueprints.mentor.routes import mentor_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(mentor_bp)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(self)")
        if os.environ.get("FLASK_ENV") == "production":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    @app.errorhandler(403)
    def forbidden(e): return render_template("errors/error.html", code=403, message="Akses tidak diizinkan."),403
    @app.errorhandler(404)
    def not_found(e): return render_template("errors/error.html", code=404, message="Halaman atau data tidak ditemukan."),404
    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/error.html", code=500, message="Terjadi kesalahan. Silakan coba kembali."),500

    with app.app_context():
        db.create_all()
        _bootstrap(app)
    return app

def _bootstrap(app):
    if User.query.filter_by(role="admin").first(): return
    credentials=[]
    admin_name=os.environ.get("SCREENFLOW_ADMIN_USERNAME","admin")
    admin_password=os.environ.get("SCREENFLOW_ADMIN_PASSWORD") or secrets.token_urlsafe(14)
    admin=User(username=admin_name,display_name="Super Admin",role="admin")
    admin.set_password(admin_password); db.session.add(admin)
    credentials.append((admin_name,admin_password))
    for i in range(1,11):
        username=f"mentor{i:02d}"; password=secrets.token_urlsafe(14)
        user=User(username=username,display_name=f"Mentor {i:02d}",role="mentor")
        user.set_password(password); user.mentor_profile=Mentor(qr_token=new_token())
        db.session.add(user); credentials.append((username,password))
    db.session.add(ScreeningPeriod(name="Periode Screening 1",description="Periode awal SCREENFLOW",is_active=True))
    db.session.commit()
    path=Path(app.instance_path)/"initial_credentials.txt"
    path.write_text("SCREENFLOW — kredensial awal (ganti password setelah login)\n\n"+"\n".join(f"{u}: {p}" for u,p in credentials)+"\n",encoding="utf-8")
    try: os.chmod(path,0o600)
    except OSError: pass
