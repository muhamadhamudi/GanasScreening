from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from app.models import Mentor
from app.services.screening_service import active_period, create_participant, ScreeningError

public_bp=Blueprint("public",__name__)

@public_bp.get("/")
def index(): return render_template("public/index.html")

@public_bp.get("/scan")
def scan(): return render_template("public/scan.html")

@public_bp.get("/api/qr/<token>/validate")
def validate_qr(token):
    mentor=Mentor.query.filter_by(qr_token=token).first()
    return {"valid": bool(mentor and mentor.user.is_active)}, 200

@public_bp.get("/s/<token>")
def screening_form(token):
    mentor=Mentor.query.filter_by(qr_token=token).first()
    if not mentor or not mentor.user.is_active: abort(404)
    period=active_period()
    return render_template("public/screening_form.html",mentor=mentor.user,period=period,token=token)

@public_bp.post("/s/<token>")
def screening_submit(token):
    mentor=Mentor.query.filter_by(qr_token=token).first()
    if not mentor or not mentor.user.is_active: abort(404)
    period=active_period()
    if not period:
        flash("Pendaftaran belum dibuka karena tidak ada periode aktif.","error")
        return redirect(url_for("public.screening_form",token=token))
    fields={k:request.form.get(k,"").strip() for k in ["name","nim","class_name","organization_experience","achievements"]}
    limits={"name":150,"nim":50,"class_name":50}
    errors=[]
    for key,value in fields.items():
        if not value: errors.append("Semua kolom wajib diisi."); break
        if key in limits and len(value)>limits[key]: errors.append(f"{key.replace('_',' ').title()} maksimal {limits[key]} karakter.")
    if errors:
        for error in errors: flash(error,"error")
        return render_template("public/screening_form.html",mentor=mentor.user,period=period,token=token,values=fields),400
    try:
        participant=create_participant(fields,mentor.user_id,period)
        return render_template("public/success.html",participant=participant)
    except ScreeningError as e:
        flash(str(e),"error")
        return render_template("public/screening_form.html",mentor=mentor.user,period=period,token=token,values=fields),409

@public_bp.get("/health")
def health(): return {"status":"ok"},200
