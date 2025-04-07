from datetime import datetime, timedelta
from src.auditoria_inss.src.gmailApi import GoogleGmailAPI
from src.auditoria_inss.src.sheetsApi import GoogleSheetsAPI
from src.auditoria_inss.src.logger import Logger

class Utils:
    def __init__(self):
        self.logger = Logger()
        self.gmail_api = GoogleGmailAPI()
        self.sheets_api = GoogleSheetsAPI()

    def catch_days_ago(self, delta=4):
        """
        Captura quatro dias atrás e quatro dias a frente.

        Argumentos:
        - [Opcional] delta (int): Quantidade de dias para trás ou para frente;

        Retorno:
        Array

        Exemplos:
        >>> catch_days_ago()
        [08/06/2024, 16/06/2024] 
        """
        actual_day = datetime.now()
        
        next_day = actual_day + timedelta(days=delta)
        next_day_str = next_day.strftime("%Y/%m/%d")

        four_days_ago = actual_day - timedelta(days=delta)
        four_days_ago_str = four_days_ago.strftime("%Y/%m/%d")

        return four_days_ago_str, next_day_str
  
    def upload_data_on_table(self, spreadsheet_id, range_name, data):
        """
        Faz upload de dados em uma aba específica

        Argumentos:
        - spreadsheet_id (str): ID da planilha que contenha a aba que desejamos colocar os dados
        - range_name (str): Nome da aba que desejamos colocar os dados
        - data (array): O array contendo os dados que ser colocados dentro da aba

        Retorno:
        Booleano

        """
        try:
            spreadsheet_id = spreadsheet_id
            range_name = range_name
            self.sheets_api.add_data_to_spreadsheet(spreadsheet_id, f'{range_name}!A1', data)
            return True
        except Exception as e:
            self.logger.error_log(str(e))
            return False