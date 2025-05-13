from flask import Flask, request, jsonify
import requests
from requests.auth import HTTPBasicAuth
import datetime
import os
import logging

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

# Configurações
OURO_BASE_URL = "https://meuappdecursos.com.br/ws/v2"
BASIC_AUTH = os.getenv("BASIC_AUTH", "SUA_API_KEY")
SUPORTE_WHATSAPP = os.getenv("SUPORTE_WHATSAPP", "61981969018")
TOKEN_UNIDADE = os.getenv("TOKEN_UNIDADE", "SEU_TOKEN_UNIDADE")

MAPEAMENTO_CURSOS = {
    "Excel PRO": [161, 197, 201],
    "Design Gráfico": [254, 751, 169],
    "Inteligência Artificial": [600, 601, 602]
}

def enviar_log_whatsapp(mensagem):
    try:
        msg_formatada = requests.utils.quote(mensagem)
        url = f"https://api.callmebot.com/whatsapp.php?phone=556186660241&text={msg_formatada}&apikey=2712587"
        resp = requests.get(url)
        if resp.status_code == 200:
            logging.info("✅ Log enviado ao WhatsApp com sucesso.")
        else:
            logging.error(f"❌ Falha ao enviar log para WhatsApp: {resp.text}")
    except Exception as e:
        logging.error(f"❌ Erro ao enviar log para WhatsApp: {str(e)}")

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        logging.info("🔔 Webhook recebido com sucesso")
        payload = request.json

        if not payload:
            return jsonify({"error": "Payload inválido"}), 400

        evento = payload.get("webhook_event_type")
        if evento != "order_approved":
            return jsonify({"message": "Evento ignorado"}), 200

        customer = payload.get("Customer", {})
        nome = customer.get("full_name")
        cpf = customer.get("CPF", "").replace(".", "").replace("-", "")
        email = customer.get("email")
        celular = customer.get("mobile") or "(00) 00000-0000"

        plano_assinatura = payload.get("Subscription", {}).get("plan", {}).get("name")
        logging.info(f"📦 Plano de assinatura: {plano_assinatura}")

        cursos_ids = MAPEAMENTO_CURSOS.get(plano_assinatura)
        if not cursos_ids:
            return jsonify({"error": f"Plano '{plano_assinatura}' não mapeado."}), 400

        # Criar aluno (usando form-data)
        dados_aluno = {
            "token": TOKEN_UNIDADE,
            "nome": nome,
            "data_nascimento": "2000-01-01",
            "email": email,
            "fone": celular,
            "senha": "123456",
            "celular": celular,
            "doc_cpf": cpf,
            "doc_rg": "00000000000",
            "pais": "Brasil"
        }

        logging.info("📨 Enviando dados do aluno para a API de cadastro...")
        resp_cadastro = requests.post(f"{OURO_BASE_URL}/alunos", data=dados_aluno, auth=HTTPBasicAuth(BASIC_AUTH, ""))
        
        if resp_cadastro.status_code != 200:
            logging.error(f"❌ Erro na criação do aluno: {resp_cadastro.text}")
            return jsonify({"error": "Falha ao criar aluno", "detalhes": resp_cadastro.text}), 500

        aluno_response = resp_cadastro.json()
        aluno_id = aluno_response.get("data", {}).get("id")
        if not aluno_id:
            return jsonify({"error": "ID do aluno não encontrado."}), 500

        logging.info(f"✅ Aluno criado com sucesso. ID: {aluno_id}")

        # Criar matrícula
        dados_matricula = {
            "token": TOKEN_UNIDADE,
            "cursos": ",".join(str(curso_id) for curso_id in cursos_ids)
        }

        logging.info(f"📨 Dados para matrícula do aluno {aluno_id}: {dados_matricula}")
        resp_matricula = requests.post(f"{OURO_BASE_URL}/alunos/matricula/{aluno_id}", data=dados_matricula, auth=HTTPBasicAuth(BASIC_AUTH, ""))
        
        if resp_matricula.status_code != 200:
            logging.error(f"❌ Erro na matrícula do aluno: {resp_matricula.text}")
            return jsonify({"error": "Falha ao matricular", "detalhes": resp_matricula.text}), 500

        logging.info("✅ Matrícula realizada com sucesso")

        return jsonify({"message": "Aluno cadastrado e matriculado com sucesso!", "aluno_id": aluno_id, "cursos": cursos_ids}), 200

    except Exception as e:
        logging.error(f"❌ EXCEÇÃO NO PROCESSAMENTO: {str(e)}")
        enviar_log_whatsapp(f"❌ Erro interno no servidor: {str(e)}")
        return jsonify({"error": "Erro interno no servidor", "detalhes": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
