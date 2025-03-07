import pandas as pd
import sys
import io
import datetime

class Intelbras():

    def __init__(self, output_filename="Planilha intelbras"):        
        self.output_filename = f"{output_filename}_{datetime.date.today().strftime('%d-%m-%Y')}"

    def run(self, file):
        
        self.extract(file)
        self.transform()
        output = self.load()
        return output

    def extract(self, excel_file):
        # converte o arquivo enviado via POST e lê os bytes
        content = excel_file.stream.read()
        excel_io = io.BytesIO(content)

        # lê a planilha e converte em um DataFrame
        self.df = pd.read_excel(excel_io, engine='openpyxl')

        # filtra o DataFrame apenas com as colunas que importam
        self.df = self.df[
            [
                'nome',
                'numero_de_telefone', 
                'AUT.Fax', 
                'AUT.Telefone celular', 
                'AUT.Contato', 
                'AUT.Contato telefone'
            ]
        ]

        # converte o DataFrame em um dicionário com listas, sendo o nome da coluna a chave e o resto da coluna uma lista [] com os dados
        self.dicionario = self.df.to_dict('list')

    def transform(self):
        # define as colunas que vão ser alteradas
        colunas_com_telefones = [
            'numero_de_telefone', 
            'AUT.Fax', 
            'AUT.Telefone celular', 
            'AUT.Contato', 
            'AUT.Contato telefone'
        ]

        # itera entre as colunas
        for coluna in colunas_com_telefones:
            # contador para guiar a alteração dos dados, fazendo o papel de índice da lista. é zerado a cada nova coluna nesse processo.
            contador = 0

            # itera entre as células de cada coluna limpando os dados
            for item in self.dicionario[coluna]:
                try:
                    # converte o conteúdo da célula em string para evitar problemas com o tipo (algumas colunas vazias estavam sendo lidas como float, objeto não iterável, causando erro.)
                    item = str(item)
                    item = "".join([numero for numero in item if numero.isdigit()]) # mantém apenas os números em cada célula, tirando textos e caracteres desnecessários
                except Exception as e:
                    # em caso de erro, printa o erro, a célula que deu problema e encerra imediatamente a execução do programa
                    print(e)
                    print(item)
                    sys.exit(0)
                else:
                    # substitui o dado anterior pelo dado limpo e incrementa o contador para passar para a próxima célula
                    self.dicionario[coluna][contador] = item
                    contador += 1

        # transforma a tabela em DataFrame novamente e continua a limpeza
        self.df = pd.DataFrame(self.dicionario)

        # resume as colunas de telefone em apenas uma, repetindo o nome do cliente
        self.df = pd.melt(self.df, id_vars=['nome'], value_name='telefone', value_vars=colunas_com_telefones)
        self.df = self.df.sort_values(['nome'])
        self.df = self.df.drop('variable', axis=1)
        self.df = self.df[self.df['telefone'].str.match(r"^5?5?\d{0,2}9?\d{8}$")]
        self.df['telefone'] = self.df['telefone'].apply(self.clean_numbers)

        # última limpeza dos dados
        self.df = self.df.dropna() # remove valores nulos que podem surgir durante o tratamento
        self.df = self.df.drop_duplicates() # remove as linhas duplicadas (mesmo cliente e mesmo número de telefone)

    def load(self):
        output = io.BytesIO()
        self.df.to_csv(output, index=False, sep=',', encoding='utf-8')
        output.seek(0)
        return output

    def clean_numbers(self, number):
        number = str(number)
        number = "".join(c for c in number if c.isdigit())
        
        if len(number) == 0:
            return "VERIFICAR"
        
        if number.startswith('55') and len(number) == 13:
            return number
        
        if len(number) == 8:
            return "55719" + number
        
        if len(number) == 9:
            return "5571" + number
        
        if len(number) == 10:
            return '55' + number[:2] + "9" + number[2:]
        
        if len(number) == 11:
            return '55' + number
        
        if number.startswith("719") and len(number) == 12:
            return "55719" + number[3:]
        
        if number.startswith("55719") and len(number) == 12:
            return "55719" + number[4:]
        
        else:
            return f"INVÁLIDO - {number}"
