from src.auditoria_inss.src.logger import Logger

import os.path
import ctypes
from sys import exit

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleSheetsAPI:

    def __init__(self):
        """
        Construtor

        - Instancia a classe Logger que servirá para manter uma linha do tempo dos acontecimentos do sistema e também para fins de debug
        - Cria o service baseado no método __auth para verificar as credenciais e retornar um service para fazer uso dos endpoints da API.
        """
        self.logger = Logger()
        self.service = self.__auth()


    def __auth(self):
        """
        Método responsável por realizar a autenticação das credenciais da API do Sheets, assim que o processo é validado ele retorna o service
        para que os endpoints da API sejam utilizados, caso o processo de validação seja mal-sucedido ele retorna o erro nos logs e exibe a mensagem na tela.
        
        Retorna:
        O service que será utilizado para as requisições no endpoint da API.

        Nota:
        - Os scopes também incluem a API do Gmail pois é a mesma credencial com as API's habilitadas.
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

            service = build('sheets', 'v4', credentials=creds)
            return service

        except Exception as e:
            ctypes.windll.user32.MessageBoxW(0, "O processo de validação das credenciais falhou, verifique a sua conexão com a internet", "Erro de Validação", 0)
            self.logger.warning_log(str(e))
            exit(0)

    def get_spreadsheet_data(self, spreadsheet_id, range_name):
        """
            Busca os dados que existem em uma aba

            Argumentos: 
            spreadsheet_id (str): ID da planilha que desejamos buscar os dados.
            range_name (str): Nome da Aba da planilha que desejamos buscar os dados.

            Retorna:
            Array

            Exemplos:
            >>> get_spreadsheet_data('KbAEHGM3pTSI31iaF35kzHCUhnE0XEgEz8L3QvDDjkog5', 'ABA COM DADOS')
            [['Nome', 'Idade', 'Sexo'], ['Eustáquio', '22', 'Masculino']]
        """
        try:
            result = self.service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
            values = result.get('values', [])
            return values
        except Exception as e:
            self.logger.warning_log(str(e))
            ctypes.windll.user32.MessageBoxW(0, f"Ocorreu um erro ao obter os dados do Google Sheets", "Erro ao Obter Dados", 0)

    def add_data_to_spreadsheet(self, spreadsheet_id, range_name, data):
        """
        Adiciona dados a uma aba

        Argumentos: 
        - spreadsheet_id (str): ID da planilha que desejamos buscar os dados.
        - range_name (str): Nome da Aba da planilha que desejamos buscar os dados.
        - data (array): Dados que desejamos inserir na planilha

        Retorna: 
        - Booleano

        Exemplos:
        >>> add_data_to_spreadsheet('2S4JXu62jkJWbKvNJHUuhz0jhB2ylXUsZKicHNZyEVO8', 'Aba Escolhida', ['Dados Célula 1', 'Dados Célula 2'])

        """

        try:
            value_range_body = {'values': data}
            request = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=value_range_body
            )

            response = request.execute()
            return response
        except HttpError as err:
            self.logger.warning_log(str(err))
            ctypes.windll.user32.MessageBoxW(None, f"Ocorreu um erro ao adicionar dados à planilha: {err}", "Erro ao Adicionar Dados", 0)

    def clear_sheet(self, spreadsheet_id, range_name):
        """
        Limpa todos os dados de uma aba

        Argumentos: 
        - spreadsheet_id (str): ID da planilha que desejamos apagar os dados.
        - range_name (str): Nome da Aba da planilha que desejamos apagar os dados.

        Exemplos:
        >>> clear_sheet('2S4JXu62jkJWbKvNJHUuhz0jhB2ylXUsZKicHNZyEVO8', 'Aba Escolhida Para Apagar')
        """
        try:
            clear_request_body = {}
            request = self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                body=clear_request_body
            )
            response = request.execute()
            return response
        except HttpError as err:
            ctypes.windll.user32.MessageBoxW(None, f"Ocorreu um erro ao limpar o conteúdo da planilha: {err}", "Erro ao Limpar Planilha", 0)
    
    def move_and_clear_sheet(self, source_spreadsheet_id, source_range, destination_spreadsheet_id, destination_range):
        """
        Limpa os dados de uma aba A recorta e cola os dados de uma aba B que pode ou não estar na mesma planilha.

        Argumentos: 
        - source_spreadsheet_id (str): ID da planilha que vamos recortar os dados
        - source_range (str): Nome da aba que vamos recortar os dados
        - destination_spreadsheet_id (str): ID da planilha de destino que vamos colar os dados
        - destination_range (str): Nome da aba de destino que vamos colar os dados

        Exemplos:
        >>> move_and_clear_sheet('2S4JXu62jkJWbKvNJHUuhz0jhB2ylXUsZKicHNZyEVO8', 'Aba com Dados', 'QdmRTuijtMkBxeXkEvEJgKrrvEyvXGvsGwmVPgANOsekV', 'Aba sem Dados')

        Nota:

        - Vale lembrar que essa função não é incremental, então ele não vai adicionar novos dados dentro da aba de destino e sim apagar os dados que existiam
        e colocar a da aba de origem.
        """
        try:
            data = self.get_spreadsheet_data(source_spreadsheet_id, source_range)
            if data != []:
                self.clear_sheet(destination_spreadsheet_id, destination_range)
                self.add_data_to_spreadsheet(destination_spreadsheet_id, destination_range, data)
                self.clear_sheet(source_spreadsheet_id, source_range)
            else:
                self.logger.error_log(message = "Não haviam dados nas planilhas de origem")
                return "Não há dados nas planilhas do dia corrente"
        except Exception as e:
            self.logger.error_log(message = f"Ocorreu um erro ao mover e limpar os dados: {str(e)}")