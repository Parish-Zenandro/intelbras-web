import logging
import os
class Logger:
    """
    Classe responsável por implementar a biblioteca "logging" mas também instanciar um logger dentro da classe de Relatório e SheetsApi.

    Para mais detalhes acesse a documentação oficial da biblioteca: 
    - https://docs.python.org/3/library/logging.html
    """
    
    def __init__(self):
        self.logger_path = os.path.join(os.getcwd(), 'src', 'auditoria_inss', 'logs', 'log.log')
        logging.basicConfig(filename=self.logger_path,level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

    def info_log(self, message):
        logging.info(message)
    
    def warning_log(self, message):
        logging.warning(message)
        
    def error_log(self, message):
        logging.error(message)