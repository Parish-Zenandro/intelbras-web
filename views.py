from flask import request, render_template, send_file, Response
from main import app
from src.intelbras import Intelbras
from src.auditoria_inss import clear_sheets_and_move_data, execucao_dos_fluxos
import datetime
from io import BytesIO
import configparser, os


@app.route("/", methods=['GET',])
def home():
    if request.method != 'GET':
        return Response(status=405)
    
    return render_template('home.html')

@app.route("/intelbras", methods=['GET', 'POST'])
def intelbras():
    if request.method == 'POST':
        try:
            script = Intelbras()
            csv = script.run(request.files['file'])
            return send_file(csv, as_attachment=True, download_name=f"planilha intelbras_{datetime.date.today().strftime('%d-%m-%Y')}.csv", mimetype='text/csv')
        except Exception as e:
            return render_template("error.html", error=str(e))
    elif request.method == 'GET':
        return render_template('intelbras.html')
    else:
        return "METHOD NOT ALLOWED"

@app.route("/auditoria", methods=['GET', 'POST'])
def auditoria():

    def get_planilha_base():
        CONFIG_FILE = os.path.join(os.getcwd(), 'src', 'auditoria_inss', 'config', 'config.ini')
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE, encoding='utf-8')
        header_sheets = config['Sheets']
        planilha_base = header_sheets["Planilha Base"]
        return planilha_base
    link_planilha = f"https://docs.google.com/spreadsheets/d/{get_planilha_base()}"

    if request.method == 'GET':
        return render_template('auditoria.html', link_planilha=link_planilha)
    
    elif request.method == 'POST':
        command = request.form['command']

        match command:

            case 'limpar_dados':
                move_data = clear_sheets_and_move_data()
                if move_data["success"]:
                    return render_template('auditoria.html', dados_movidos=move_data["success"], link_planilha=link_planilha)
                else:
                    return render_template('auditoria.html', dados_movidos=move_data["success"], link_planilha=link_planilha, error=move_data["error"])
                
            case 'enviar_diferenca':
                file = request.files['lpra']
                file_bytes = BytesIO(file.read())
                success = execucao_dos_fluxos(planilha_lpra=file_bytes)
                if not success["success"]:
                    return render_template('auditoria.html', error=success["error"], link_planilha=link_planilha)
                return render_template('auditoria.html', success=success["success"], message=success["message"], link_planilha=link_planilha)
            
    else:
        return render_template('auditoria.html', link_planilha=link_planilha)


@app.route("/auditoria/changelog")
def auditoria_changelog():
    if request.method != 'GET':
        return Response(status=405)
    return render_template('auditoria_changelog.html')
