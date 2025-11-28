import sys
import os
import re
from flask import Flask
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.models import session, Investimentos  

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
DB_PATH = os.path.join(BASE_DIR, "..", "API", "instance", "banco.db")
DB_PATH = os.path.abspath(DB_PATH)
print(BASE_DIR)
print(DB_PATH)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"


def get_investments():
    rendafixa = session.query(Investimentos).all()
    rendas = []
    for renda in rendafixa:
        if 'MASTER' in renda.titulo:
            continue
        rendas.append(
            {
                'id': renda.id,
                'titulo': renda.titulo,
                'vencimento': renda.vencimento,
                'valor mínimo': renda.valor_minimo,
                'taxa': renda.taxa,
                'liquidez': renda.liquidez,
                'tipo': renda.tipo
            }
        )
        
    return rendas

def filter_investments(titulo, vencimento, valor_minimo, tipo, rentabilidade, liquidez_diaria):
    hoje = date.today()
    all_investiments = get_investments()
    filtered_investments = []
    approve = 0
    truthy = 0
    for investment in all_investiments:
        if titulo:
            truthy += 1
            if titulo.lower() in investment.get('titulo').lower():
                approve += 1
        if vencimento:
            vencimento = int(vencimento)
            truthy += 1
            if 'dias' in investment.get('vencimento'):
                dias_vencimento = int(investment.get('vencimento').split()[0])
                dias_no_mes = 30.45
                if vencimento >= round(dias_vencimento/dias_no_mes):
                    approve += 1
            else:              
                data1 = datetime.strptime(investment.get('vencimento'), '%d/%m/%Y')
                data2 = datetime.strptime(str(hoje), '%Y-%m-%d')

                diferenca = relativedelta(data1, data2)
                total_meses = diferenca.years * 12 + diferenca.months
                if total_meses <= vencimento:
                    approve += 1
        if rentabilidade:
            truthy += 1
            if rentabilidade == 'Pré-Fixado' and re.match(r'^\d+,\d{2}%$', investment.get('taxa')):
                approve += 1
            elif rentabilidade == 'IPCA' and 'IPCA' in investment.get('taxa'):
                approve += 1
            elif rentabilidade == 'Pós-Fixado' and ('CDI' in investment.get('taxa') or 'SELIC' in investment.get('taxa')):
                approve +=1
        if valor_minimo:
            valor = float(valor_minimo)
            investment_minimum_value = float(investment.get('valor mínimo').replace("R$", "").replace(".", "").replace(",", ".").strip())
            truthy += 1
            if valor >= investment_minimum_value:
                approve +=1 
        if tipo:
            truthy +=1
            if investment.get('tipo') == tipo:
                approve += 1
        if liquidez_diaria:
            truthy +=1
            if liquidez_diaria == 'sim' and 'Diária' in investment.get('liquidez'):
                approve +=1
            elif liquidez_diaria == 'não' and not 'Diária' in investment.get('liquidez'):
                approve += 1

        if approve == truthy:
            filtered_investments.append(investment)
        truthy = 0
        approve = 0
    return filtered_investments

def converter_taxa(taxa_str, percentage = False):
        CDI = 0.149   
        SELIC = 0.1525
        IPCA = 0.043
        if not percentage:
            taxa_str = taxa_str.replace(',', '.').strip().upper()
        if "CDI" in taxa_str and "%" in taxa_str and "+" not in taxa_str:
            if percentage:
                num = percentage
            else:
                num = float(re.findall(r"[\d.]+", taxa_str)[0])
            return (num / 100) * CDI

        elif "CDI" in taxa_str and "+" in taxa_str:
            num = float(re.findall(r"[\d.]+", taxa_str.split('+')[1])[0])
            return CDI + (num / 100)

        elif "IPCA" in taxa_str:
            if percentage:
                num = percentage
            else:
                num = float(re.findall(r"[\d.]+", taxa_str.split('+')[1])[0])
                if '+' in taxa_str:
                    return IPCA + (num / 100)
                else:
                    num = float(re.findall(r"[\d.]+", taxa_str)[0])
            return (num / 100) * IPCA    

        elif "SELIC".lower() in taxa_str.lower():
            if percentage:
                num = percentage
            else:
                num = float(re.findall(r"[\d.]+", taxa_str.split('+')[1])[0])
                if '+' in taxa_str:
                    return SELIC + (num / 100)
                else:
                    num = float(re.findall(r"[\d.]+", taxa_str)[0])
            return (num / 100) * SELIC            

        elif ("%" in taxa_str and not percentage) or ("Prefixado" in taxa_str):
            print(taxa_str)
            if percentage: 
                num = percentage
            else:
                num = float(re.findall(r"[\d.]+", taxa_str)[0])
            return num / 100
        
        elif "Poupança" in taxa_str:
            return percentage / 100
        else:
            return None
    
def filtrar_investimentos(investimentos, usuario):  
    investimentos_filtrados = []
    prazo_meses = int(usuario.get('prazo'))
    prazo_em_dias = prazo_meses * 30.5
    valor_inicial = float(usuario.get('valor_inicial', 0))
    hoje = datetime.today()
    prazo_final = hoje + relativedelta(months=prazo_meses)

    for renda in investimentos:
        vencimento = renda['vencimento']
        liquidez = renda['liquidez'].lower()
        valor_minimo_str = renda['valor mínimo']

        prazo_ok = False
        if 'dias' in vencimento:
            try:
                dias_vencimento = int(vencimento.split()[0])
                prazo_ok = dias_vencimento <= prazo_em_dias
            except:
                continue
        else:
            try:
                data_obj = datetime.strptime(vencimento, "%d/%m/%Y")
                prazo_ok = data_obj <= prazo_final
            except:
                continue

        if not prazo_ok:
            continue

        if usuario.get('liquidez_diaria'):
            if 'diária' not in liquidez:
                continue
    
        try:
            valor_minimo_float = float(valor_minimo_str.replace('R$', '').replace('.', '').replace(',', '.').strip())
            if valor_inicial < valor_minimo_float:
                continue
        except:
            continue

        investimentos_filtrados.append(renda)
    return investimentos_filtrados

def calcular_lucros(investimentos, usuario):
    resultados = []

    for inv in investimentos:
        taxa = converter_taxa(inv['taxa'])
        valor_inicial = float(usuario["valor_inicial"])
        valor_mensal = float(usuario["valor_mensal"])
        prazo = int(usuario["prazo"])            
        valor_final_bruto = calcular_rendimento(
            valor_inicial,
            valor_mensal,
            prazo,
            taxa
        )
        total_investido = valor_inicial + valor_mensal * prazo
        lucro_bruto = valor_final_bruto - total_investido
        imposto = calcular_ir(inv["tipo"], prazo, lucro_bruto)
        lucro_liquido = lucro_bruto - imposto
        valor_final_liquido = total_investido + lucro_liquido

        resultados.append({
            **inv,
            "valor_final_bruto": round(valor_final_bruto, 2),
            "valor_final_liquido": round(valor_final_liquido, 2),
            "lucro_bruto": round(lucro_bruto, 2),
            "lucro_liquido": round(lucro_liquido, 2),
            "imposto_pago": round(imposto, 2),
            "total_investido": total_investido
        })

    return resultados
    
def calcular_ir(tipo_investimento, prazo_meses, lucro):
    tipo = tipo_investimento.lower()

    isentos = ['lci', 'cra', 'cri', 'lig', 'poupança']
    if any(i in tipo.lower() for i in isentos):
        return 0.0  

    dias = prazo_meses * 30
    if dias <= 180:
        aliquota = 0.225
    elif dias <= 360:
        aliquota = 0.20
    elif dias <= 720:
        aliquota = 0.175
    else:
        aliquota = 0.15

    return lucro * aliquota

def calcular_rendimento(valor_inicial, aporte_mensal, meses, taxa_anual):
        
        taxa_mensal = (1 + taxa_anual) ** (1/12) - 1
        valor_futuro = valor_inicial * (1 + taxa_mensal) ** meses + aporte_mensal * ((1 + taxa_mensal) ** meses - 1) / taxa_mensal
        return round(valor_futuro, 2)

