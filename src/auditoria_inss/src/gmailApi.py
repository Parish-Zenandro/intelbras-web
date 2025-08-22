from src.auditoria_inss.src.logger import Logger
from sys import exit
import ctypes
import os
from datetime import datetime
import base64

from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from time import sleep

class GoogleGmailAPI():

    def __init__(self):
        """
        Método construtor da classe responsável por instanciar o objeto Logger para fins de garantir o log dos acontecimentos e também
        responsável por instanciar o service que será utilizado pela API do Gmail, esse processo está diretamente ligado com o __auth que
        faz a verificação das credenciais no arquivo /credentials, validando se estas são válidas
        """
        self.logger = Logger()
        self.service = self.__auth()

    def __auth(self):
        """
        Método responsável por realizar a autenticação das credenciais da API do Gmail, assim que o processo é validado ele retorna o service
        para que os endpoints da API sejam utilizados, caso o processo de validação seja mal-sucedido ele retorna o erro nos logs e exibe a mensagem na tela.
        
        Retorna:
        O service que será utilizado para as requisições no endpoint da API.

        Nota:
        - Os scopes também incluem a API do Sheets pois é a mesma credencial com as API's habilitadas.
        - As credenciais estão vinculadas diretamente com o e-mail: roboemailinss@pz.adv.br.
        """

        try:
            SCOPES = ["https://www.googleapis.com/auth/spreadsheets", 'https://www.googleapis.com/auth/gmail.modify']
            creds = None
            TOKEN_PATH = os.path.join(os.getcwd(), 'src', 'auditoria_inss', 'credentials', 'token.json')
            CREDS_PATH = os.path.join(os.getcwd(), 'src', 'auditoria_inss', 'credentials', 'credentials.json')

            if os.path.exists(TOKEN_PATH):
                creds = Credentials.from_authorized_user_file(TOKEN_PATH)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())

                else:
                    flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
                    creds = flow.run_local_server(port=0)

                with open(TOKEN_PATH, 'w') as token:
                    token.write(creds.to_json())
            
            service = build('gmail', 'v1', credentials=creds)
            return service

        except Exception as e:
            self.logger.error_log(str(e))
            return "O processo de validação das credenciais falhou"


    def get_protocols_numbers(self, query):
        """
            Função responsável por: 
            Capturar todos os número de processos enviados para o e-mail: roboemailinss@pz.adv.br na query solicitada
            que o assunto comece com "[INSS] O status do requerimento" presente na linha 92 e diferente de pendentes

            Contexto:
            - O assunto é importante que comeece com "[INSS] O status do requerimento" pois muito outros tipos de e-mail são enviados para a máscara
            sendo assim podendo poluir visualmente e trazer dados errôneos. 
            - Os pendentes não são de interesse pois são apenas um aviso de o INSS precisa confirmar algo.

            Argumentos:
            query (str): A query que será solicitada na caixa de busca do e-mail retornando todos que vierem naquela seleção.

            Retorna:
            array: Todos os números de processo.

            Exemplos:
            >>> get_protocols_numbers("CONCLUÍDA after:01/01/2024 before:01/02/2024")
            [1909234, 1294212, 2912848, 991292, ...]
        """

        try:
            self.protocols = set()
            page_token = None

            while True:
                results = self.service.users().messages().list(
                    userId='me', 
                    q=query,
                    maxResults=100,
                    pageToken=page_token
                ).execute()
                messages = results.get('messages', [])

                if not messages:
                    break

                for message in messages:
                    message_id = message['id']

                    message_details = self.service.users().messages().get(
                        userId='me', 
                        id=message_id, 
                        format='metadata',
                        metadataHeaders=['Subject']
                    ).execute()
                    subject = next(
                        (header['value'] for header in message_details['payload']['headers']),
                        "",
                    )

                    if "[INSS] O status do requerimento" in subject:
                        subject_parts = subject.split(' ')
                        protocol, status = subject_parts[5], subject_parts[9]
                        
                        if (status != "Pendente"):
                            self.protocols.add(protocol)

                page_token = results.get('nextPageToken')
                if not page_token:
                    break

                sleep(1)

            return list(self.protocols) if self.protocols else None

        except Exception as e:
            self.logger.error_log(str(e))
            return "Ocorreu um erro na leitura dos e-mails"
        
    def get_LPRA_spreadsheet(self):
        pass


    def send_log_to_emails(self, log_message, emails):

        """
        Envia uma mensagem específica para os emails passados no parâmetro.

        Argumentos:
        - log_message (str): Message a ser enviada para os emails
        - emails (array): Lista dos emails para onde a mensagem será enviada

        Vale lembrar que o subtitulo será sempre "Log Auditoria - Data de execução" para fins de controle.

        """
        
        message = MIMEText(log_message)
        message['to'] = ', '.join(emails)
        message['from'] = 'roboemailinsss@pz.adv.br'
        message['subject'] = f'Log Auditoria - {datetime.now().strftime("%d/%m/%Y")}'
        raw_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")}

        sended_message = self.service.users().messages().send(userId="me", body=raw_message).execute()
