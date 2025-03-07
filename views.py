from flask import request, render_template, send_file
from main import app
from src.intelbras import Intelbras
import datetime

@app.route("/", methods=['GET', 'POST'])
def intelbras():
    if request.method == 'POST':
        script = Intelbras()
        csv = script.run(request.files['file'])
        return send_file(csv, as_attachment=True, download_name=f"planilha intelbras_{datetime.date.today().strftime('%d-%m-%Y')}.csv", mimetype='text/csv')
    elif request.method == 'GET':
        return render_template('home.html')
    else:
        return "METHOD NOT ALLOWED"
