from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from openpyxl import Workbook

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.get("https://apprendafixa.com.br/app/investimentos/rendafixa?tipo=tesourodireto")
abas = driver.find_elements(By.CSS_SELECTOR, ".mat-tab-labels > div")[2:-2]
dados_aba = {}  

def get_investments():
    for idx, aba in enumerate(abas):
        try:
            aba.click()
            time.sleep(2)
            nome_aba = aba.text.strip()
        
            if (aba.text == 'CCB' or aba.text == 'LC'):
                continue
            cards = driver.find_elements(By.CSS_SELECTOR, "mat-card.mat-focus-indicator.container.dark-card")
            lista_cards = []
            for card in cards:
                values = card.find_elements(By.CLASS_NAME, 'value')
                valor_minimo = values[0].text
                vencimento = values[4].text
                if (aba.text == 'Tesouro Direto'):
                    nome_titulo = card.find_element(By.TAG_NAME, 'mat-card-title').text
                    taxa = card.find_element(By.CSS_SELECTOR, '.taxa p').text
                    liquidez = 'Diária'
                else:
                    nome_titulo = card.find_element(By.TAG_NAME, 'mat-card-subtitle').text
                    taxa = card.find_element(By.CSS_SELECTOR, '.taxa p span').text
                    liquidez = values[5].text

                lista_cards.append({
                        "Título": nome_titulo,
                        "Valor Mínimo": valor_minimo,
                        "Vencimento": vencimento,
                        "Liquidez": liquidez,
                        "Taxa": taxa
                    })

            dados_aba[nome_aba] = lista_cards

        except Exception as e:
            print(f"Erro na aba {idx+1}: {e}")
    return dados_aba

if __name__ == '__main__':
    dados_aba = get_investments()
