from src.auditoria_inss.src.sheetsApi import GoogleSheetsAPI
from src.auditoria_inss.src.gmailApi import GoogleGmailAPI
from src.auditoria_inss.utils import Utils
from src.auditoria_inss.src.logger import Logger
import numpy as np
import configparser
import pandas as pd

import subprocess
from sys import exit
import os
from datetime import datetime, timedelta

logger = Logger()
CONFIG_FILE = os.path.join(os.getcwd(), 'src', 'auditoria_inss', 'config', 'config.ini')
config = configparser.ConfigParser()
config.read(CONFIG_FILE, encoding='utf-8')



if 'Gmail' in config or 'Sheets' in config:
    header_sheets = config['Sheets']

    planilha_base = header_sheets["Planilha Base"]

    exigencia_dia_anterior = header_sheets["Nome da Aba Exigencia Dia Anterior"]
    exigencia_dia_corrente = header_sheets["Nome da Aba Exigencia Dia Corrente"]

    analise_dia_anterior = header_sheets["Nome da Aba Em Analise Dia Anterior"]
    analise_dia_corrente = header_sheets["Nome da Aba Em Analise Dia Corrente"]

    aba_matriz = header_sheets['Nome da Aba Matriz']

    planilha_auditoria = header_sheets["Planilha Auditoria"]

    concluidos_sem_email = header_sheets["Nome da Aba de Concluidos sem Email"]
    exigencias_sem_email = header_sheets["Nome da Aba de Exigencias sem Email"]

    prox_exibicao = header_sheets['Próximo dia de Exibição de Repetidas']

    header_gmail = config['Gmail']
    emails = [n.strip()
              for n in header_gmail['lista de emails do log'].split(',')]
else:
    logger.error_log(
        "Configurações do Sheets não encontrado no arquivo de configuração.")
    exit(0)


sheets_api = GoogleSheetsAPI()
gmail_api = GoogleGmailAPI()
utils = Utils()

concluded_protocols = []
requirements_protocols = []


def clear_sheets_and_move_data():
    """
    Movimenta os dados do dia corrente para o dia anterior, assim deixando a planilha utilizada pronta para receber novos dados.
    """
    try:
        sheets_api.move_and_clear_sheet(
            planilha_base,
            exigencia_dia_corrente,
            planilha_base,
            exigencia_dia_anterior)
        sheets_api.move_and_clear_sheet(
            planilha_base,
            analise_dia_corrente,
            planilha_base,
            analise_dia_anterior)
    except Exception as e:
        logger.error_log(
            'Ocorreu um erro ao tentar movimentar os dados do dia corrente para o dia anterior. \n Erro:' +
            str(e))
        return {"success": False, "error": str(e)}

    return {"success": True, "sheet_url": f"https://docs.google.com/spreadsheets/d/{planilha_base}"}


def analisar_concluidos_planilha_auditoria():
    """
    Analisa a planilha Em análise e movimenta para a planilha de Acompanhamento Auditoria.

    Sua função principal consiste em:
    - Buscar todos os números processos dos últimos quatro dias que foram concluídos e enviados para o e-mail (roboemailinss@pz.adv.br) afim de evitar duplo-envio.
    - Analisar os números de processo que existem na aba de Em análise - Dia Anterior e não existem nas abas Em Análise - Dia Corrente, Exigência dia Corrente.

    Assim os dados retornados são enviados para a planilha de auditoria automaticamente.

    Contexto:
    O processo dentro do portal do INSS transita em 4 fases, Exigência, Em análise, Cancelado ou Concluído, logo se o processo não está nem em Em análise nem em Exigência
    ele pode estar em Concluído ou Cancelado, pela quantidade de Canceladas serem baixas inferimos que ele está em Concluído.
    """
    try:
        data_atual = datetime.now().strftime("%d/%m/%Y")

        # Coleta os processos concluídos até delta dias atrás no e-mail
        time_interval = utils.catch_days_ago(delta=7)
        start_date = time_interval[0]
        end_date = time_interval[1]
        query = f'CONCLUÍDA after:{start_date} before:{end_date}'
        protocols_on_email = gmail_api.get_protocols_numbers(query)

        # Coleta os dados das planilhas
        requirement_before = [
            n for n in sheets_api.get_spreadsheet_data(
                planilha_base,
                f'{exigencia_dia_anterior}!A:F')]
        requirement_after = [
            n for n in sheets_api.get_spreadsheet_data(
                planilha_base,
                f'{exigencia_dia_corrente}!A:F')]

        analysis_before = [
            n for n in sheets_api.get_spreadsheet_data(
                planilha_base,
                f'{analise_dia_anterior}!A:F')]
        analysis_after = [
            n for n in sheets_api.get_spreadsheet_data(
                planilha_base,
                f'{analise_dia_corrente}!A:F')]

        data = []

        analysis_after_protocols = [n[0] for n in analysis_after]
        requirement_after_protocols = [n[0] for n in requirement_after]

        # Itera sobre os dados da planilha em análise do dia anterior
        for client_data in analysis_before:
            process_number = client_data[0]
            benefit_type = client_data[1]

            # Se o processo não está em análise no dia corrente nem em
            # exigências no dia corrente nem no e-mail, trata como concluido
            if process_number not in analysis_after_protocols and process_number not in requirement_after_protocols and process_number not in protocols_on_email:
                # Armazena o número de protocolo e o tipo de benefício para
                # enviar por e-mail posteriormente
                concluded_protocols.append([process_number, benefit_type])

                # Guarda na memória para inserir na planilha
                client_data.insert(0, data_atual)
                data.append(client_data)

        # Itera sobre os processos com exigências do dia anterior
        for client_data in requirement_before:
            process_number = client_data[0]
            # Se o processo não está em análise no dia corrente nem nas
            # exigências do dia corrente nem no e-mail, trata como concluido
            if process_number not in analysis_after_protocols and process_number not in requirement_after_protocols and process_number not in protocols_on_email:
                concluded_protocols.append([process_number, benefit_type])

                client_data.insert(0, data_atual)
                data.append(client_data)

        # Insere na planilha
        utils.upload_data_on_table(
            planilha_auditoria, concluidos_sem_email, data)
        logger.info_log('O processo de envio dos dados de CONCLUÍDAS para planilha de Auditoria foi realizada com sucesso!')
        return {"success": True, "message": 'O processo de envio dos dados de CONCLUÍDAS para planilha de Auditoria foi realizada com sucesso!'}
    except Exception as e:
        logger.error_log('O processo de envio dos dados de CONCLUÍDAS para planilha de Auditoria não foi realizado, ocorreu um erro:' +
            str(e))
        return {"success": False, "error": str(e)}

# Análise de concluídos para serem enviados para a planilha "MATRIZ INSS"


def analisar_concluidos_planilha_base():
    """
    Analisa a planilha Em análise e movimenta para a aba "MATRIZ INSS".

    Sua função principal consiste em:
    - Analisar os números de processo que existem na aba de Em análise - Dia Anterior e não existem nas abas Em Análise - Dia Corrente, Exigência dia Corrente.

    Assim os dados retornados são enviados para a planilha de auditoria automaticamente.

    Contexto:
    - Essa tabela de Matriz existe para fins de controle se o número de processos que existem na MATRIZ INSS também existem no porta do INSS
    """
    try:
        data_atual = datetime.now().strftime("%d/%m/%Y")

        # Coleta a planilha de exigência dia anterior
        requirement_before = [
            n for n in sheets_api.get_spreadsheet_data(
                planilha_base,
                f'{exigencia_dia_anterior}!A:F')]
        # Coleta a planilha de exigência dia corrente
        requirement_after = [
            n for n in sheets_api.get_spreadsheet_data(
                planilha_base,
                f'{exigencia_dia_corrente}!A:F')]

        # Coleta a planilha de processos em análise do dia anterior
        analysis_before = [
            n for n in sheets_api.get_spreadsheet_data(
                planilha_base,
                f'{analise_dia_anterior}!A:F')]
        # Coleta a planilha de processos em análise do dia corrente
        analysis_after = [
            n for n in sheets_api.get_spreadsheet_data(
                planilha_base,
                f'{analise_dia_corrente}!A:F')]

        # Coleta a matriz de concluídos
        database = [
            n for n in sheets_api.get_spreadsheet_data(
                planilha_base,
                f'{aba_matriz}!A:F')]

        data_matriz = []

        analysis_after_protocols = [n[0] for n in analysis_after if n]
        requirement_after_protocols = [n[0] for n in requirement_after if n]
        database_protocols = [n[0] for n in database if n]

        # Itera sobre cada linha dos processos em análise do dia anterior
        for client_data in analysis_before:
            process_number = client_data[0]
            # Se o número de protocolo não existir na planilha em análise dia
            # anterior nem na de exigências dia corrente nem na aba matriz,
            # adiciona a data de hoje na linha e guarda na memória para inserir
            # como concluída
            if process_number not in analysis_after_protocols and process_number not in requirement_after_protocols and process_number not in database_protocols:
                client_data.append(data_atual)
                data_matriz.append(client_data)

        # Itera sobre cada linha dos processos em exigência do dia anterior
        for client_data in requirement_before:
            process_number = client_data[0]
            # Se o número de protocolo não existir na planilha em análise do
            # dia anterior nem na de exigência do dia corrente nem na aba
            # matriz, adiciona a data de hoje na linha e guarda na memória para
            # inserir como concluída
            if process_number not in requirement_after_protocols and process_number not in database_protocols:
                client_data.append(data_atual)
                data_matriz.append(client_data)

        # Insere as linhas reservadas na variável data_matriz na aba matriz da
        # planilha INSS Relação
        utils.upload_data_on_table(planilha_base, aba_matriz, data_matriz)
        logger.info_log('O processo de envio dos dados para planilha Base foi realizada com sucesso!')
        return {"success": True, "message": 'O processo de envio dos dados para planilha Base foi realizada com sucesso!'}
    
    except Exception as e:
        logger.error_log(f'Erro: O processo de envio dos dados para planilha Base não foi realizado! {str(e)}')
        return {"success": False, "error": str(e)}

# Análise de Exigências do dia corrente


def analisar_exigencias(df_lpra):
    """
    Analisa a planilha Exigência e movimenta para a planilha de Acompanhamento Auditoria.

    Sua função principal consiste em:
    - Buscar todos os números processos dos últimos quatro dias que foram exigência e enviados para o e-mail (roboemailinss@pz.adv.br) afim de evitar duplo-envio.
    - Analisa a planilha enviada por e-mail (esta deve ser inserida na pasta Planilhas)
    - Compara a planilha enviada por e-mail com os processos da aba Exigência - Dia corrente e capturar apenas os valores que não existem na planilha enviada por e-mail
    - Em seguida compara com as exigências do dia anterior retirando aquelas que se repetem nos dois a fim de exibir apenas as novas exigências.

    Detalhe:
    - Quando o exibir_repetidos for igual a verdadeiro (True) todos os processos que se repetem entre as duas planilhas serão exibidas pois podem ser uma nova exigência.

    Assim os dados retornados são enviados para a planilha de auditoria automaticamente.

    Contexto:
    A regra foi criada desta forma devido uma grande quantidade de exigências que estavam na fase perícia e continuavam constando com exigências para o portal
    assim trazendo os mesmos processos todos os dias gerando uma quantidade maior do que de fato deveria, sendo assim foi criada a variável
    exibir_repetidas que de 7 em 7 dias é alterada na configuração automaticamente, então de semana em semana todos os processos serão exibidos.

    """
    try:

        exibir_repetidos = False

        data_atual = datetime.now().strftime("%d/%m/%Y")

        # Busca no e-mail os processos em exigência
        query = f'EXIGÊNCIA after:{utils.catch_days_ago(delta=7)[0]} before:{utils.catch_days_ago()[1]}'
        protocols_on_email = gmail_api.get_protocols_numbers(query)

        if not protocols_on_email:
            protocols_on_email = []
        # Verifica se já passaram 7 dias desde a última análise de processos
        # com exigência
        if (datetime.strptime(prox_exibicao, '%d/%m/%Y') <= datetime.now()):
            exibir_repetidos = True  # Volta a analisar os processos que estavam com exigência

            # Configura próxima data de exibição e insere no arquivo config.ini
            proxima_data_de_exibicao = (
                datetime.now() +
                timedelta(
                    days=7)).strftime("%d/%m/%Y")
            config.set(
                'Sheets',
                'Próximo dia de Exibição de Repetidas',
                proxima_data_de_exibicao)
            with open(CONFIG_FILE, 'w+', encoding='utf-8') as configfile:
                config.write(configfile)

        # Coleta os processos em exigência nas planilhas dos dias corrente e
        # anterior
        requerimentos_dia_corrente = [
            n for n in sheets_api.get_spreadsheet_data(
                planilha_base, f'{exigencia_dia_corrente}!A:F')]
        requerimentos_dia_anterior = [
            n[0] for n in sheets_api.get_spreadsheet_data(
                planilha_base, f'{exigencia_dia_anterior}!A:F')]
        
        # Lê a planilha do CPJ e coleta os números de protocolo que o CPJ já possui
        lpra_protocols = df_lpra['PRO.Número do processo'].dropna()
        numeros_de_processo_na_planilha = [str(int(n)) for n in lpra_protocols.values]
        dados_do_portal = []

        # Itera sobre os dados dos processos com exigências do dia corrente
        for dados_do_cliente in requerimentos_dia_corrente:
            numero_de_processo = dados_do_cliente[0]
            tipo_de_beneficio = dados_do_cliente[1]

            if exibir_repetidos:

                # Se o número de protocolo não estiver na planilha do CPJ nem
                # nos registros do e-mail, guarda na memória.
                if numero_de_processo not in numeros_de_processo_na_planilha and numero_de_processo not in protocols_on_email:

                    # Guarda o número do processo e tipo de benefício para
                    # enviar as logs por e-mail
                    requirements_protocols.append(
                        [numero_de_processo, tipo_de_beneficio])

                    # Insere a data atual nos dados do cliente (linha da
                    # tabela) e guarda na variável dados_do_portal
                    dados_do_cliente.insert(0, data_atual)
                    dados_do_portal.append(dados_do_cliente)
            else:

                # Se o número de protocolo não estiver na planilha do CPJ nem
                # nas exigências do dia anterior nem nos registros do e-mail,
                # guarda na memória.
                if numero_de_processo not in numeros_de_processo_na_planilha and numero_de_processo not in requerimentos_dia_anterior and numero_de_processo not in protocols_on_email:

                    # Guarda o número do processo e tipo de benefício para
                    # enviar as logs por e-mail
                    requirements_protocols.append(
                        [numero_de_processo, tipo_de_beneficio])

                    # Insere a data atual nos dados do cliente (linha da
                    # tabela) e guarda na variável dados_do_portal
                    dados_do_cliente.insert(0, data_atual)
                    dados_do_portal.append(dados_do_cliente)

        # Insere os dados_do_portal na aba de exigências sem e-mail da planilha
        # Auditoria INSS
        utils.upload_data_on_table(
            planilha_auditoria,
            exigencias_sem_email,
            dados_do_portal)

        logger.info_log('O processo de envio dos dados de EXIGÊNCIA para planilha de Auditoria foi realizada com sucesso!')
        return {"success": True, "message": 'O processo de envio dos dados de EXIGÊNCIA para planilha de Auditoria foi realizada com sucesso!'}

    except Exception as e:
        logger.error_log('O processo de envio dos dados de EXIGÊNCIA para planilha de Auditoria não foi realizado, ocorreu um erro:' + str(e))
        return {"success": False, "error": str(e)}


def execucao_dos_fluxos(planilha_lpra):
    """
    Script que executa os 3 processos um após o outro apenas se alguma planilha estiver presente dentro da pasta "Planilhas" afim de evitar que o operador
    execute o script sem colocar na pasta a planilha que é enviada por email.
    """
    planilha = planilha_lpra

    planilha_presente = True if planilha else False
    
    if planilha_presente:
        try:
            df_lpra = pd.read_excel(planilha)

            analise_concluidos_planilha_base = analisar_concluidos_planilha_base()
            if not analise_concluidos_planilha_base['success']:
                return analise_concluidos_planilha_base
            
            analise_concluidos_planilha_auditoria = analisar_concluidos_planilha_auditoria()
            if not analise_concluidos_planilha_auditoria['success']:
                return analise_concluidos_planilha_auditoria
            
            analise_exigencias = analisar_exigencias(df_lpra=df_lpra)
            if not analise_exigencias['success']:
                return analise_exigencias
            
            envio_de_logs = enviar_log()
            if not envio_de_logs["success"]:
                return envio_de_logs
            
        except Exception as e:
            Logger.error_log('Erro: ' + str(e))
            return {"success": False, "error": str(e)}
        else: 
            return {"success": True, "message": "Processos movimentados com sucesso! Verifique o log no e-mail"}
    else:
        logger.error_log(
            'O usuário não enviou a planilha de LPRA')
        return {"success": False, "error": 'O usuário não enviou a planilha de LPRA'}


def estruturar_mensagem_de_log():
    """
    Função responsável por estruturar a mensagem que será enviada para os e-mails cadastrados como forma de log.

    Retorno:
    - str()

    Exemplos:
    >>> estruturar_mensagem_de_log()
    "Log Auditoria - 12/06/2024
    Dados movimentados p/ CONCLUÍDOS SEM EMAIL:

    000000

    Quantidade: 1

    Dados movimentados p/ EXIGÊNCIAS SEM EMAIL:

    0000001

    Quantidade: 1
    """

    data_atual = datetime.now().strftime("%d/%m/%Y")
    message = f"Log Auditoria - {data_atual}"

    message += "\n\nDados movimentados p/ CONCLUÍDOS SEM EMAIL: \n\n"
    for concluded, benefit_type in concluded_protocols:
        message += f"{concluded} - {benefit_type}\n"
    message += f"Quantidade total: {len(concluded_protocols)}"

    message += "\n\nDados movimentados p/ EXIGÊNCIAS SEM EMAIL: \n\n"
    for requirement, benefit_type in requirements_protocols:
        message += f"{requirement} - {benefit_type}\n"
    message += f"Quantidade total: {len(requirements_protocols)}"

    return message


def enviar_log():
    """
    Envia o log de todos os emails que foram encontrados na diferença de planilhas, tanto concluídos quanto exigência para os emails cadastrados
    no arquivo de configuração.
    """
    try:
        gmail_api.send_log_to_emails(estruturar_mensagem_de_log(), emails)
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": True, "message": 'O processo de envio da mensagem de logs foi realizado com sucesso! Você pode fechar o programa agora.'}


