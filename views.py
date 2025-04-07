from flask import request, render_template, send_file, Response
from main import app
from src.intelbras import Intelbras
from src.auditoria_inss import clear_sheets_and_move_data, execucao_dos_fluxos
import datetime
from io import BytesIO


@app.route("/", methods=['GET',])
def home():
    if request.method != 'GET':
        return Response(status=405)
    
    return render_template('home.html')

@app.route("/intelbras", methods=['GET', 'POST'])
def intelbras():
    if request.method == 'POST':
        script = Intelbras()
        csv = script.run(request.files['file'])
        return send_file(csv, as_attachment=True, download_name=f"planilha intelbras_{datetime.date.today().strftime('%d-%m-%Y')}.csv", mimetype='text/csv')
    elif request.method == 'GET':
        return render_template('intelbras.html')
    else:
        return "METHOD NOT ALLOWED"

@app.route("/auditoria", methods=['GET', 'POST'])
def auditoria():
    if request.method == 'GET':
        return render_template('auditoria.html')
    elif request.method == 'POST':
        command = request.form['command']
        print(command)
        match command:
            case 'limpar_dados':
                move_data = clear_sheets_and_move_data()
                if move_data["success"]:
                    return render_template('auditoria.html', dados_movidos=move_data["success"], link_planilha=move_data["sheet_url"])
                else:
                    return render_template('auditoria.html', dados_movidos=move_data["success"], link_planilha=None, error=move_data["error"])
            case 'enviar_diferenca':
                # A PLANILHA AGORA É ENVIADA VIA POST. SALVAR EM MEMÓRIA E ATUALIZAR O SCRIPT DE EXECUÇÃO DO ROBÔ!
                file = request.files['lpra']
                file_bytes = BytesIO(file.read())
                success = execucao_dos_fluxos(planilha_lpra=file_bytes)
                if not success["success"]:
                    return render_template('auditoria.html', error=success["error"])
                return render_template('auditoria.html', success=success["success"], message=success["message"])
    else:
        return render_template('auditoria.html')

