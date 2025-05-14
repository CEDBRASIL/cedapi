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

# DADOS PARA TOKEN DE UNIDADE
API_URL = "https://meuappdecursos.com.br/ws/v2/unidades/token/"
ID_UNIDADE = 4158
KEY = "e6fc583511b1b88c34bd2a2610248a8c"

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


def enviar_log_whatsapp(mensagem):
    try:
        msg_formatada = requests.utils.quote(mensagem)
        url = f"https://api.callmebot.com/whatsapp.php?phone={CALLMEBOT_PHONE}&text={msg_formatada}&apikey={CALLMEBOT_APIKEY}"
        requests.get(url)
    except Exception as e:
        print("❌ Falha ao enviar log:", str(e))


def obter_token_unidade():
    try:
        resposta = requests.get(f"{API_URL}{ID_UNIDADE}", auth=HTTPBasicAuth(KEY, ""))
        dados = resposta.json()
        if dados.get("status") == "true":
            return dados["data"]["token"]
        else:
            enviar_log_whatsapp("❌ Erro ao obter token da unidade: " + str(dados))
    except Exception as e:
        enviar_log_whatsapp(f"❌ Erro de conexão ao obter token: {str(e)}")
    return None


@app.before_request
def log_request():
    print(f"\n📥 {request.method} - {request.url}")


@app.route("/secure", methods=["GET", "HEAD"])
def secure():
    return "", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        payload = request.json
        evento = payload.get("webhook_event_type")
        if evento != "order_approved":
            return jsonify({"message": "Evento ignorado"}), 200

        customer = payload.get("Customer", {})
        nome = customer.get("full_name")
        cpf = customer.get("CPF", "").replace(".", "").replace("-", "")
        email = customer.get("email")
        celular = customer.get("mobile") or ""
        cidade = customer.get("city") or ""
        estado = customer.get("state") or ""
        endereco = f"{customer.get('street', '')}, {customer.get('number', '')}"
        bairro = customer.get("neighborhood", "")
        complemento = customer.get("complement", "")
        cep = customer.get("zipcode", "")

        plano = payload.get("Subscription", {}).get("plan", {}).get("name")
        cursos_ids = MAPEAMENTO_CURSOS.get(plano)

        if not cursos_ids:
            return jsonify({"error": f"Plano '{plano}' não mapeado."}), 400

        token_unidade = obter_token_unidade()
        if not token_unidade:
            return jsonify({"error": "Token da unidade não pôde ser obtido"}), 500

        dados_aluno = {
            "token": token_unidade,
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

        resp = requests.post(f"{OURO_BASE_URL}/alunos", data=dados_aluno, headers={
            "Authorization": f"Basic {BASIC_AUTH}"
        })

        resp_data = resp.json()
        if not resp.ok or resp_data.get("status") != "true":
            enviar_log_whatsapp(f"❌ Falha no cadastro: {resp.text}")
            return jsonify({"error": "Falha ao cadastrar aluno"}), 500

        aluno_id = resp_data["data"]["id"]

        dados_matricula = {
            "token": token_unidade,
            "cursos": ",".join(map(str, cursos_ids))
        }

        matricula_resp = requests.post(f"{OURO_BASE_URL}/alunos/matricula/{aluno_id}", data=dados_matricula, headers={
            "Authorization": f"Basic {BASIC_AUTH}"
        })

        matricula_data = matricula_resp.json()
        if not matricula_resp.ok or matricula_data.get("status") != "true":
            enviar_log_whatsapp(f"❌ Falha na matrícula: {matricula_resp.text}")
            return jsonify({"error": "Falha ao matricular aluno"}), 500

        msg_boas_vindas = (
            f"Oii {nome}, Seja bem Vindo/a Ao CED BRASIL\n\n"
            f"📦 *Plano adquirido:* {plano}\n\n"
            "*Seu acesso:*\n"
            f"Login: *{cpf}*\n"
            "Senha: *123456*\n\n"
            "🌐 *Portal do aluno:* https://ead.cedbrasilia.com.br\n"
            "📲 *App Android:* https://play.google.com/store/apps/details?id=br.com.om.app&hl=pt_BR\n"
            "📱 *App iOS:* https://apps.apple.com/br/app/meu-app-de-cursos/id1581898914\n\n"
            f"📞 *Suporte:* {SUPORTE_WHATSAPP}"
        )

        numero_whatsapp = "55" + ''.join(filter(str.isdigit, celular))[-11:]
        requests.post(CHATPRO_URL, json={
            "number": numero_whatsapp,
            "message": msg_boas_vindas
        }, headers={
            "Authorization": CHATPRO_TOKEN,
            "Content-Type": "application/json"
        })

        enviar_log_whatsapp(f"✅ Aluno {nome} cadastrado e matriculado com sucesso.")
        return jsonify({"message": "Aluno cadastrado e matriculado com sucesso"}), 200

    except Exception as e:
        enviar_log_whatsapp(f"❌ Erro geral: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
