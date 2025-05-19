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

        if not os.path.exists(os.path.join(os.getcwd(), 'src', 'auditoria_inss', 'logs')):
            os.mkdir(os.path.join(os.getcwd(), 'src', 'auditoria_inss', 'logs'))
            
        if not os.path.exists(self.logger_path):
            with open(self.logger_path, 'x') as file:
                file.write("")

        logging.basicConfig(filename=self.logger_path,level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

    def info_log(self, message):
        logging.info(message)
    
    def warning_log(self, message):
        logging.warning(message)
        
    def error_log(self, message):
        logging.error(message)