from core.models import Investimentos, session

def inserir_dados(dados_scraping):

    for key, values in dados_scraping.items():
        for value in values:
            investimento = Investimentos(
                titulo=value.get('Título'),
                valor_minimo=value.get('Valor Mínimo'),
                vencimento=value.get('Vencimento'),
                taxa=value.get('Taxa'),
                liquidez=value.get('Liquidez'),
                tipo=key
            )
            session.add(investimento)

    session.commit()
    print("Dados inseridos com sucesso!")
