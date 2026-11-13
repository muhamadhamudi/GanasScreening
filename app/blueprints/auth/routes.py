from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User

auth_bp=Blueprint("auth",__name__)

@auth_bp.route("/admin/login",methods=["GET","POST"])
def admin_login(): return _login("admin")

@auth_bp.route("/mentor/login",methods=["GET","POST"])
def mentor_login(): return _login("mentor")

def _login(role):
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard" if current_user.role=="admin" else "mentor.dashboard"))
    if request.method=="POST":
        username=request.form.get("username","").strip(); password=request.form.get("password","")
        user=User.query.filter_by(username=username,role=role,is_active=True).first()
        if user and user.check_password(password):
            login_user(user,remember=False,fresh=True)
            return redirect(url_for("admin.dashboard" if role=="admin" else "mentor.dashboard"))
        flash("Username atau password salah, atau akun tidak aktif.","error")
    return render_template("auth/login.html",role=role)

@auth_bp.post("/logout")
@login_required
def logout():
    logout_user(); flash("Anda berhasil logout.","success")
    return redirect(url_for("public.index"))
