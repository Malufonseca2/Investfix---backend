from flask import Flask, jsonify, request
from flask_cors import CORS
from API import controller
import sys
import os
import google.generativeai as genai
from datetime import date

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://malufonseca2.github.io",
            "http://localhost:3000",
            "http://localhost:3001",
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})


genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
hoje = date.today()

@app.route('/investments', methods=['GET', 'POST'])
def get_all_investments():
    if request.method == 'GET':
        return controller.get_investments()
    elif request.method == 'POST':
        request_payload = request.get_json(force=True).get('body')

        titulo = request_payload.get('titulo')
        vencimento = request_payload.get('vencimento')
        valor_minimo = request_payload.get('valor_minimo')
        tipo = request_payload.get('tipo')
        rentabilidade = request_payload.get('rentabilidade')
        liquidez_diaria = request_payload.get('liquidez_diaria')        

        return controller.filter_investments(titulo, vencimento, valor_minimo, tipo, rentabilidade, liquidez_diaria)

@app.route('/calculate', methods=['POST'])
def calculate_best_investment():
    request_payload = request.get_json(force=True).get('body')
    usuario = request_payload
    investimentos = controller.get_investments()

    filtrados = controller.filtrar_investimentos(investimentos, usuario)
    if len(filtrados) == 0:
        return 'Sem investimentos que atendam a esses critérios!' 
    resultados = controller.calcular_lucros(filtrados, usuario)
    top3 = sorted(resultados, key=lambda x: x["lucro_liquido"], reverse=True)[:3]
    model = genai.GenerativeModel("gemini-2.5-flash")  
    if usuario.get('liquidez_diaria') == 'sim':
        liquidez = 'Precisa de liquidez diária'
    else: 
        liquidez = 'Não precisa de liquidez diária'

    
    prompt= f'''Eu posso investir inicialmente {usuario.get('valor_inicial')} reais, {usuario.get('valor_mensal')} reais por mês por {usuario.get('prazo')} meses. 
    {liquidez} e o objetivo com esse investimento é {usuario.get('objetivo')}. Qual dos investimentos {top3}, é o melhor para mim? Apenas retorne o índice, sem texto'''
    response = model.generate_content(prompt)
    texto = int(response.text.replace('\n', ','))
    
    return jsonify(top3[texto])

@app.route('/compare', methods=['POST'])
def compare_revenues():
    request_payload = request.get_json(force=True).get('body')
    usuario = request_payload.get('usuario')
    investimentos = request_payload.get('investimentos')
    resultados = []
    for key, value in investimentos.items():
        taxa = controller.converter_taxa(key, int(value))
        valor_inicial = float(usuario["Valor inicial"].replace("R$", "").replace(".", "").replace(",", ".").strip())
        valor_mensal = float(usuario["Aporte mensal"].replace("R$", "").replace(".", "").replace(",", ".").strip())
        prazo = int(usuario['Meses investindo']) 
        valor_final_bruto = controller.calcular_rendimento(
            valor_inicial,
            valor_mensal,
            prazo,
            taxa
        )
        total_investido = valor_inicial + valor_mensal * prazo
        lucro_bruto = valor_final_bruto - total_investido
        imposto = controller.calcular_ir(key, prazo, lucro_bruto)
        lucro_liquido = lucro_bruto - imposto
        valor_final_liquido = total_investido + lucro_liquido
        def formatar_brl(valor):
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        resultados.append({
            "tipo": key,
            "valor_final_bruto": formatar_brl(valor_final_bruto) ,
            "valor_final_liquido": round(valor_final_liquido, 2),
            "lucro_bruto": formatar_brl(lucro_bruto),
            "lucro_liquido": formatar_brl(lucro_liquido),
            "imposto_pago": formatar_brl(imposto),
            "total_investido": formatar_brl(total_investido)
        })
    return resultados
