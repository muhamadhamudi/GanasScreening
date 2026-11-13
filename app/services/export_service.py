import csv, io
from flask import Response
from app.models import Participant

def csv_export(query):
    output=io.StringIO(newline="")
    writer=csv.writer(output)
    writer.writerow(["Nama","NIM","Kelas","Pengalaman Organisasi","Prestasi","Nama Mentor","Status","Catatan Mentor","Tanggal Screening","Tanggal Keputusan","Periode"])
    for p in query.order_by(Participant.created_at.desc()).all():
        writer.writerow([p.name,p.nim,p.class_name,p.organization_experience,p.achievements,p.mentor.display_name,p.status,p.mentor_note,p.created_at.isoformat() if p.created_at else "",p.reviewed_at.isoformat() if p.reviewed_at else "",p.period.name])
    return Response("\ufeff"+output.getvalue(), mimetype="text/csv; charset=utf-8", headers={"Content-Disposition":"attachment; filename=screenflow-participants.csv"})
