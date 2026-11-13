from functools import wraps
from flask import Blueprint, render_template, request, jsonify, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.models import Participant, ScreeningAuditLog
from app.services.statistics_service import counts
from app.services.screening_service import review_participant, ScreeningError

mentor_bp=Blueprint("mentor",__name__,url_prefix="/mentor")
def mentor_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*a,**kw):
        if current_user.role!="mentor": abort(403)
        return fn(*a,**kw)
    return wrapped

def own_query(): return Participant.query.filter_by(mentor_id=current_user.id)

def filtered_query():
    q=own_query(); term=request.args.get("q","").strip(); status=request.args.get("status","")
    if term: q=q.filter(or_(Participant.name.ilike(f"%{term}%"),Participant.nim.ilike(f"%{term}%")))
    if status in ("Pending","Lolos","Tidak Lolos"): q=q.filter_by(status=status)
    return q


@mentor_bp.get("/dashboard")
@mentor_required
def dashboard():
    q=own_query(); participants=q.order_by(Participant.created_at.desc()).limit(12).all()
    return render_template("mentor/dashboard.html",stats=counts(q),participants=participants)

@mentor_bp.get("/participants")
@mentor_required
def participants():
    page=max(1,request.args.get("page",1,type=int)); pagination=filtered_query().order_by(Participant.created_at.desc()).paginate(page=page,per_page=15,error_out=False)
    return render_template("mentor/participants.html",pagination=pagination)

@mentor_bp.get("/participants/<int:participant_id>")
@mentor_required
def participant_detail(participant_id):
    p=own_query().filter_by(id=participant_id).first_or_404()
    logs=ScreeningAuditLog.query.filter_by(participant_id=p.id).order_by(ScreeningAuditLog.created_at.desc()).all()
    return render_template("mentor/detail.html",p=p,logs=logs)

@mentor_bp.post("/participants/<int:participant_id>/review")
@mentor_required
def review(participant_id):
    p=own_query().filter_by(id=participant_id).first_or_404()
    try: review_participant(p,current_user,request.form.get("status",""),request.form.get("mentor_note","")); flash("Keputusan screening berhasil disimpan.","success")
    except ScreeningError as e: flash(str(e),"error")
    return redirect(url_for("mentor.participant_detail",participant_id=p.id))

@mentor_bp.get("/api/updates")
@mentor_required
def updates():
    q=own_query(); return jsonify({"stats":counts(q),"latest_id":q.with_entities(Participant.id).order_by(Participant.id.desc()).scalar() or 0,"participants":[{"id":p.id,"name":p.name,"nim":p.nim,"status":p.status,"created_at":p.created_at.isoformat()} for p in q.order_by(Participant.created_at.desc()).limit(10).all()]})

@mentor_bp.route("/profile",methods=["GET","POST"])
@mentor_required
def profile():
    if request.method=="POST":
        display=request.form.get("display_name","").strip(); password=request.form.get("password","")
        if display and len(display)<=150: current_user.display_name=display
        if password:
            if len(password)<10: flash("Password minimal 10 karakter.","error"); return redirect(url_for("mentor.profile"))
            current_user.set_password(password)
        from app.extensions import db
        db.session.commit(); flash("Profil diperbarui.","success")
    return render_template("mentor/profile.html")
