from functools import wraps
from datetime import date
from flask import Blueprint, render_template, request, abort, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models import User, Mentor, Participant, ScreeningPeriod, ScreeningAuditLog
from app.services.qr_service import new_token, screening_url, qr_png_bytes
from app.services.statistics_service import counts, mentor_summary
from app.services.export_service import csv_export

admin_bp=Blueprint("admin",__name__,url_prefix="/admin")
def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*a,**kw):
        if current_user.role!="admin": abort(403)
        return fn(*a,**kw)
    return wrapped

def participant_query():
    q=Participant.query; term=request.args.get("q","").strip(); status=request.args.get("status",""); mentor=request.args.get("mentor",type=int); period=request.args.get("period",type=int)
    if term: q=q.join(User,Participant.mentor_id==User.id).filter(or_(Participant.name.ilike(f"%{term}%"),Participant.nim.ilike(f"%{term}%")))
    if status in ("Pending","Lolos","Tidak Lolos"): q=q.filter_by(status=status)
    if mentor: q=q.filter_by(mentor_id=mentor)
    if period: q=q.filter_by(period_id=period)
    return q


@admin_bp.get("/dashboard")
@admin_required
def dashboard():
    q=Participant.query; return render_template("admin/dashboard.html",stats=counts(q),summaries=mentor_summary(),recent=q.order_by(Participant.created_at.desc()).limit(10).all(),periods=ScreeningPeriod.query.order_by(ScreeningPeriod.id.desc()).all())

@admin_bp.route("/mentors",methods=["GET","POST"])
@admin_required
def mentors():
    if request.method=="POST":
        username=request.form.get("username","").strip(); name=request.form.get("display_name","").strip(); password=request.form.get("password","")
        if not username or not name or len(password)<10 or User.query.filter_by(username=username).first(): flash("Data tidak valid, username mungkin sudah digunakan, atau password kurang dari 10 karakter.","error")
        else:
            u=User(username=username,display_name=name,role="mentor"); u.set_password(password); u.mentor_profile=Mentor(qr_token=new_token()); db.session.add(u); db.session.commit(); flash("Mentor berhasil dibuat.","success")
        return redirect(url_for("admin.mentors"))
    return render_template("admin/mentors.html",mentors=User.query.filter_by(role="mentor").order_by(User.display_name).all())

@admin_bp.post("/mentors/<int:user_id>/update")
@admin_required
def update_mentor(user_id):
    u=User.query.filter_by(id=user_id,role="mentor").first_or_404(); name=request.form.get("display_name","").strip(); username=request.form.get("username","").strip(); password=request.form.get("password","")
    duplicate=User.query.filter(User.username==username,User.id!=u.id).first()
    if not name or not username or duplicate or (password and len(password)<10): flash("Periksa nama, username, atau password.","error")
    else:
        u.display_name=name; u.username=username
        if password: u.set_password(password)
        db.session.commit(); flash("Data mentor diperbarui.","success")
    return redirect(url_for("admin.mentors"))

@admin_bp.post("/mentors/<int:user_id>/toggle")
@admin_required
def toggle_mentor(user_id):
    u=User.query.filter_by(id=user_id,role="mentor").first_or_404(); u.is_active=not u.is_active; db.session.commit(); flash("Status mentor diperbarui.","success"); return redirect(url_for("admin.mentors"))

@admin_bp.post("/mentors/<int:user_id>/qr/reset")
@admin_required
def reset_qr(user_id):
    u=User.query.filter_by(id=user_id,role="mentor").first_or_404(); u.mentor_profile.qr_token=new_token(); db.session.commit(); flash("QR token lama telah dibatalkan.","success"); return redirect(url_for("admin.mentors"))

@admin_bp.get("/mentors/<int:user_id>/qr.png")
@admin_required
def mentor_qr(user_id):
    u=User.query.filter_by(id=user_id,role="mentor").first_or_404(); from io import BytesIO
    return send_file(BytesIO(qr_png_bytes(screening_url(u.mentor_profile.qr_token))),mimetype="image/png",as_attachment=False,download_name=f"screenflow-{u.username}-qr.png")

@admin_bp.get("/participants")
@admin_required
def participants():
    page=max(1,request.args.get("page",1,type=int)); pagination=participant_query().order_by(Participant.created_at.desc()).paginate(page=page,per_page=20,error_out=False)
    return render_template("admin/participants.html",pagination=pagination,mentors=User.query.filter_by(role="mentor").all(),periods=ScreeningPeriod.query.all())

@admin_bp.get("/participants/<int:participant_id>")
@admin_required
def participant_detail(participant_id):
    p=Participant.query.get_or_404(participant_id); logs=ScreeningAuditLog.query.filter_by(participant_id=p.id).order_by(ScreeningAuditLog.created_at.desc()).all(); return render_template("admin/detail.html",p=p,logs=logs)

@admin_bp.route("/settings",methods=["GET","POST"])
@admin_required
def settings():
    if request.method=="POST":
        action=request.form.get("action")
        if action=="period":
            name=request.form.get("name","").strip()
            if name:
                ScreeningPeriod.query.update({ScreeningPeriod.is_active:False})
                db.session.add(ScreeningPeriod(name=name,description=request.form.get("description","").strip(),is_active=True)); db.session.commit(); flash("Periode baru dibuat dan diaktifkan.","success")
        elif action=="activate":
            period=ScreeningPeriod.query.get_or_404(request.form.get("period_id",type=int)); ScreeningPeriod.query.update({ScreeningPeriod.is_active:False}); period.is_active=True; db.session.commit(); flash("Periode aktif diperbarui.","success")
        return redirect(url_for("admin.settings"))
    return render_template("admin/settings.html",periods=ScreeningPeriod.query.order_by(ScreeningPeriod.id.desc()).all())

@admin_bp.route("/profile",methods=["GET","POST"])
@admin_required
def profile():
    if request.method=="POST":
        display=request.form.get("display_name","").strip(); password=request.form.get("password","")
        if not display or len(display)>150:
            flash("Nama tampilan wajib diisi (maksimal 150 karakter).","error")
        elif password and len(password)<10:
            flash("Password minimal 10 karakter.","error")
        else:
            current_user.display_name=display
            if password: current_user.set_password(password)
            db.session.commit(); flash("Profil Super Admin diperbarui.","success")
        return redirect(url_for("admin.profile"))
    return render_template("admin/profile.html")

@admin_bp.get("/export")
@admin_required
def export(): return csv_export(participant_query())
