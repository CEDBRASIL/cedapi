from flask import Flask, request, jsonify
import requests
from requests.auth import HTTPBasicAuth
import datetime
import os
import logging

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

# CONFIGURAÇÕES FIXAS - Variáveis de ambiente para maior segurança
OURO_BASE_URL = "https://meuappdecursos.com.br/ws/v2"
BASIC_AUTH = os.getenv("BASIC_AUTH", "ZTZmYzU4MzUxMWIxYjg4YzM0YmQyYTI2MTAyNDhhOGM6")
SUPORTE_WHATSAPP = os.getenv("SUPORTE_WHATSAPP", "61981969018")
DATA_FIM = (datetime.datetime.now() + datetime.timedelta(days=180)).strftime("%Y-%m-%d")

CHATPRO_TOKEN = os.getenv("CHATPRO_TOKEN", "566fa7beb56fc88e10a0176bbd27f639")
CHATPRO_INSTANCIA = "chatpro-xcpvtq83bk"
CHATPRO_URL = f"https://v5.chatpro.com.br/{CHATPRO_INSTANCIA}/api/v1/send_message"

CALLMEBOT_APIKEY = os.getenv("CALLMEBOT_APIKEY", "2712587")
CALLMEBOT_PHONE = os.getenv("CALLMEBOT_PHONE", "556186660241")

MAPEAMENTO_CURSOS = {
    "Excel PRO": [161, 197, 201],
    "Design Gráfico": [254, 751, 169],
    "Analista de Tecnologia da Informação (TI)": [590, 176, 239, 203],
    "Administração": [129, 198, 156, 154],
    "Inglês Fluente": [263, 280, 281],
    "Operador de Micro": [333, 334, 335],
    "Inteligência Artificial": [600, 601, 602],
    "Marketing Digital": [555, 556, 557],
    "teste": [161, 201],
    "Example plan": [161, 201]
}

API_URL = "https://meuappdecursos.com.br/ws/v2/unidades/token/"
ID_UNIDADE = 4158
KEY = os.getenv("API_KEY", "e6fc583511b1b88c34bd2a2610248a8c")

def enviar_log_whatsapp(mensagem):
    try:
        msg_formatada = requests.utils.quote(mensagem)
        url = f"https://api.callmebot.com/whatsapp.php?phone={CALLMEBOT_PHONE}&text={msg_formatada}&apikey={CALLMEBOT_APIKEY}"
        resp = requests.get(url)
        if resp.status_code == 200:
            logging.info("✅ Log enviado ao WhatsApp com sucesso.")
        else:
            logging.error(f"❌ Falha ao enviar log para WhatsApp: {resp.text}")
    except Exception as e:
        logging.error(f"❌ Erro ao enviar log para WhatsApp: {str(e)}")

def obter_token_unidade():
    try:
        resposta = requests.get(f"{API_URL}{ID_UNIDADE}", auth=HTTPBasicAuth(KEY, ""))
        resposta.raise_for_status()
        dados = resposta.json()
        if dados.get("status") == "true":
            return dados.get("data")["token"]
        logging.error(f"❌ Erro ao obter token: {dados}")
        enviar_log_whatsapp(f"❌ Erro ao obter token da unidade: {dados}")
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Exceção ao obter token: {str(e)}")
        enviar_log_whatsapp(f"❌ Exceção ao obter token: {str(e)}")
    return None

TOKEN_UNIDADE = obter_token_unidade()
if not TOKEN_UNIDADE:
    raise Exception("Token da unidade não pôde ser obtido. Verifique as credenciais.")

@app.before_request
def log_request_info():
    logging.info(f"📥 Requisição recebida: {request.url}")
    logging.info(f"📍 Método: {request.method}")
    logging.info(f"📦 Cabeçalhos: {dict(request.headers)}")

@app.route('/secure', methods=['GET', 'HEAD'])
def secure_check():
    return '', 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        logging.info("🔔 Webhook recebido com sucesso")
        payload = request.json

        if not payload:
            return jsonify({"error": "Payload inválido ou não recebido"}), 400

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

        dados_aluno = {
            "token": TOKEN_UNIDADE,
            "nome": nome,
            "data_nascimento": "2000-01-01",
            "email": email,
            "fone": celular,
            "senha": "123456",
            "celular": celular,
            "doc_cpf": cpf,
            "pais": "Brasil"
        }

        logging.info("📨 Enviando dados do aluno para a API de cadastro...")
        resp_cadastro = requests.post(f"{OURO_BASE_URL}/alunos", json=dados_aluno, headers={"Authorization": f"Basic {BASIC_AUTH}"})
        resp_cadastro.raise_for_status()
        aluno_response = resp_cadastro.json()

        aluno_id = aluno_response.get("data", {}).get("id")
        if not aluno_id:
            return jsonify({"error": "ID do aluno não encontrado."}), 500

        logging.info(f"✅ Aluno criado com sucesso. ID: {aluno_id}")

        dados_matricula = {"token": TOKEN_UNIDADE, "cursos": ",".join(str(curso_id) for curso_id in cursos_ids)}
        logging.info(f"📨 Dados para matrícula do aluno {aluno_id}: {dados_matricula}")
        resp_matricula = requests.post(f"{OURO_BASE_URL}/alunos/matricula/{aluno_id}", json=dados_matricula, headers={"Authorization": f"Basic {BASIC_AUTH}"})
        resp_matricula.raise_for_status()

        logging.info("✅ Matrícula realizada com sucesso")

        return jsonify({"message": "Aluno cadastrado e matriculado com sucesso!", "aluno_id": aluno_id, "cursos": cursos_ids}), 200

    except Exception as e:
        logging.error(f"❌ EXCEÇÃO NO PROCESSAMENTO: {str(e)}")
        enviar_log_whatsapp(f"❌ Erro interno no servidor: {str(e)}")
        return jsonify({"error": "Erro interno no servidor", "detalhes": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
