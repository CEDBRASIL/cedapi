from flask import Flask, request, jsonify
import requests
from requests.auth import HTTPBasicAuth
import datetime
import os

app = Flask(__name__)

# CONFIGURAÇÕES FIXAS
OURO_BASE_URL = "https://meuappdecursos.com.br/ws/v2"
BASIC_AUTH = "ZTZmYzU4MzUxMWIxYjg4YzM0YmQyYTI2MTAyNDhhOGM6"
SUPORTE_WHATSAPP = "61981969018"
DATA_FIM = (datetime.datetime.now() + datetime.timedelta(days=180)).strftime("%Y-%m-%d")

CHATPRO_TOKEN = "566fa7beb56fc88e10a0176bbd27f639"
CHATPRO_INSTANCIA = "chatpro-xcpvtq83bk"
CHATPRO_URL = f"https://v5.chatpro.com.br/{CHATPRO_INSTANCIA}/api/v1/send_message"

CALLMEBOT_APIKEY = "2712587"
CALLMEBOT_PHONE = "556186660241"

MAPEAMENTO_CURSOS = {
    "Excel PRO": [161, 197, 201],
    "Design Gráfico": [254, 751, 169],
    "Analista de Tecnologia da Informação (TI)": [590, 176, 239, 203],
    "Administração": [129, 198, 156, 154],
    "Inglês Fluente": [263, 280, 281],
    "Operador de Micro": [130, 599, 161, 160, 162],
    "Inteligência Artificial": [619, 734, 836],
    "Marketing Digital": [734, 236, 441, 199, 780],
    "teste": [161, 201],
    "Example plan": [161, 201]
}

API_URL = "https://meuappdecursos.com.br/ws/v2/unidades/token/"
ID_UNIDADE = 4158
KEY = "e6fc583511b1b88c34bd2a2610248a8c"

def enviar_log_whatsapp(mensagem):
    try:
        msg_formatada = requests.utils.quote(str(mensagem)[:4000])  # máximo permitido
        url = f"https://api.callmebot.com/whatsapp.php?phone={CALLMEBOT_PHONE}&text={msg_formatada}&apikey={CALLMEBOT_APIKEY}"
        requests.get(url)
    except Exception as e:
        print("❌ Erro ao enviar log para WhatsApp:", str(e))

def obter_token_unidade():
    try:
        resposta = requests.get(API_URL + f"{ID_UNIDADE}", auth=HTTPBasicAuth(KEY, ""))
        dados = resposta.json()
        if dados.get("status") == "true":
            return dados.get("data")["token"]
        enviar_log_whatsapp(f"❌ Erro ao obter token: {dados}")
    except Exception as e:
        enviar_log_whatsapp(f"❌ Exceção ao obter token: {str(e)}")
    return None

TOKEN_UNIDADE = obter_token_unidade()
if not TOKEN_UNIDADE:
    raise Exception("Token da unidade não pôde ser obtido. Verifique as credenciais.")

@app.before_request
def log_request_info():
    print("\n📥 Requisição recebida:")
    print("🔗 URL completa:", request.url)
    print("📍 Método:", request.method)
    print("📦 Cabeçalhos:", dict(request.headers))

@app.route('/secure', methods=['GET', 'HEAD'])
def secure_check():
    return '', 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        print("\n🔔 Webhook recebido com sucesso")
        payload = request.json

        # 📩 REGISTRO COMPLETO DO JSON RECEBIDO
        enviar_log_whatsapp(f"📨 Webhook recebido:\n{payload}")

        order = payload.get("order", {})
        evento = order.get("webhook_event_type")

        if evento != "order_approved":
            return jsonify({"message": f"Evento '{evento}' ignorado"}), 200

        customer = order.get("Customer", {})
        nome = customer.get("full_name")
        cpf = customer.get("CPF", "").replace(".", "").replace("-", "")
        email = customer.get("email")
        celular = customer.get("mobile") or "(00) 00000-0000"
        cidade = customer.get("city") or ""
        estado = customer.get("state") or ""
        endereco = (customer.get("street") or "") + ", " + str(customer.get("number") or "")
        bairro = customer.get("neighborhood") or ""
        complemento = customer.get("complement") or ""
        cep = customer.get("zipcode") or ""

        plano_assinatura = order.get("Subscription", {}).get("plan", {}).get("name")
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
            "doc_rg": "00000000000",
            "pais": "Brasil",
            "uf": estado,
            "cidade": cidade,
            "endereco": endereco,
            "complemento": complemento,
            "bairro": bairro,
            "cep": cep
        }

        resp_cadastro = requests.post(
            f"{OURO_BASE_URL}/alunos",
            data=dados_aluno,
            headers={"Authorization": f"Basic {BASIC_AUTH}"}
        )

        aluno_response = resp_cadastro.json()
        if not resp_cadastro.ok or aluno_response.get("status") != "true":
            erro_msg = f"❌ ERRO NO CADASTRO: {resp_cadastro.text}"
            enviar_log_whatsapp(erro_msg)
            return jsonify({"error": "Falha ao criar aluno", "detalhes": resp_cadastro.text}), 500

        aluno_id = aluno_response.get("data", {}).get("id")
        if not aluno_id:
            erro_msg = f"❌ ID do aluno não retornado! CPF: {cpf}"
            enviar_log_whatsapp(erro_msg)
            return jsonify({"error": "ID do aluno não encontrado."}), 500

        dados_matricula = {
            "token": TOKEN_UNIDADE,
            "cursos": ",".join(str(curso_id) for curso_id in cursos_ids)
        }

        resp_matricula = requests.post(
            f"{OURO_BASE_URL}/alunos/matricula/{aluno_id}",
            data=dados_matricula,
            headers={"Authorization": f"Basic {BASIC_AUTH}"}
        )

        if not resp_matricula.ok or resp_matricula.json().get("status") != "true":
            erro_msg = f"❌ ERRO NA MATRÍCULA do aluno {nome}, CPF: {cpf}, cursos: {cursos_ids}"
            enviar_log_whatsapp(erro_msg)
            return jsonify({"error": "Falha ao matricular", "detalhes": resp_matricula.text}), 500

        enviar_log_whatsapp(f"✅ MATRÍCULA OK: {nome} - CPF: {cpf}")

        mensagem = (
            f"Oii {nome}, Seja bem Vindo/a Ao CED BRASIL\n\n"
            f"📦 *Plano adquirido:* {plano_assinatura}\n\n"
            "*Seu acesso:*\n"
            f"Login: *{cpf}*\n"
            "Senha: *123456*\n\n"
            "🌐 *Portal do aluno:* https://ead.cedbrasilia.com.br\n"
            "📲 *App Android:* https://play.google.com/store/apps/details?id=br.com.om.app\n"
            "📱 *App iOS:* https://apps.apple.com/br/app/meu-app-de-cursos/id1581898914\n\n"
            f"📞 *Suporte:* {SUPORTE_WHATSAPP}"
        )

        numero_whatsapp = "55" + ''.join(filter(str.isdigit, celular))[-11:]
        resp_whatsapp = requests.post(
            CHATPRO_URL,
            json={"number": numero_whatsapp, "message": mensagem},
            headers={
                "Authorization": CHATPRO_TOKEN,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )

        if resp_whatsapp.status_code != 200:
            enviar_log_whatsapp(f"❌ Erro ao enviar WhatsApp: {resp_whatsapp.text}")

        return jsonify({
            "message": "Aluno cadastrado, matriculado e notificado com sucesso!",
            "aluno_id": aluno_id,
            "cursos": cursos_ids
        }), 200

    except Exception as e:
        erro_msg = f"❌ EXCEÇÃO NO PROCESSAMENTO: {str(e)}"
        print(erro_msg)
        enviar_log_whatsapp(erro_msg)
        return jsonify({"error": "Erro interno no servidor", "detalhes": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
