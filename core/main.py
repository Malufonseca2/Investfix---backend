from core.inserter import inserir_dados
from core.scrapper import get_investments

def main():

    dados = get_investments()
    inserir_dados(dados)

if __name__ == '__main__':
    main()
