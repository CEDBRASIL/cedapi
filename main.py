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
KEY = "e6fc583511b1b88c34bd2a2610248a8c"

# Obter token de unidade apenas uma vez
def obter_token_unidade():
    try:
        resposta = requests.get(API_URL + f"{ID_UNIDADE}", auth=HTTPBasicAuth(KEY, ""))
        dados = resposta.json()
        if dados.get("status") == "true":
            return dados.get("data")["token"]
        print("❌ Erro ao obter token:", dados)
    except Exception as e:
        print("❌ Exceção ao obter token:", str(e))
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

@app.route('/webhook', methods=['POST'])
def webhook():
    print("\n🔔 Webhook recebido com sucesso")
    payload = request.json
    evento = payload.get("webhook_event_type")

    if evento != "order_approved":
        return jsonify({"message": "Evento ignorado"}), 200

    customer = payload.get("Customer", {})
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

    print("\n📋 Dados do cliente recebidos:")
    print(f"👤 Nome: {nome}\n📧 Email: {email}\n📱 Celular: {celular}\n📄 CPF: {cpf}")
    print(f"🏩 Cidade: {cidade}\n🏡 Endereço: {endereco}\n🪩 Bairro: {bairro}\n📦 Complemento: {complemento}\n📬 CEP: {cep}\n🌍 Estado: {estado}")

    plano_assinatura = payload.get("Subscription", {}).get("plan", {}).get("name")
    print(f"📦 Plano de assinatura: {plano_assinatura}")

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

    print("📨 Enviando dados do aluno para a API de cadastro...")
    resp_cadastro = requests.post(
        f"{OURO_BASE_URL}/alunos",
        data=dados_aluno,
        headers={"Authorization": f"Basic {BASIC_AUTH}"}
    )

    aluno_response = resp_cadastro.json()
    print("📨 Resposta completa do cadastro:", aluno_response)

    if not resp_cadastro.ok or aluno_response.get("status") != "true":
        print("❌ Erro no cadastro do aluno:", resp_cadastro.text)
        return jsonify({"error": "Falha ao criar aluno", "detalhes": resp_cadastro.text}), 500

    aluno_id = aluno_response.get("data", {}).get("id")
    if not aluno_id:
        print("❌ ID do aluno não retornado!")
        return jsonify({"error": "ID do aluno não encontrado na resposta de cadastro."}), 500

    print(f"✅ Aluno criado com sucesso. ID: {aluno_id}")

    dados_matricula = {
        "token": TOKEN_UNIDADE,
        "cursos": ",".join(str(curso_id) for curso_id in cursos_ids)
    }

    print(f"📨 Dados para matrícula do aluno {aluno_id}: {dados_matricula}")
    resp_matricula = requests.post(
        f"{OURO_BASE_URL}/alunos/matricula/{aluno_id}",
        data=dados_matricula,
        headers={"Authorization": f"Basic {BASIC_AUTH}"}
    )

    if not resp_matricula.ok or resp_matricula.json().get("status") != "true":
        print("❌ Erro na matrícula:", resp_matricula.text)
        return jsonify({"error": "Falha ao matricular", "detalhes": resp_matricula.text}), 500

    print(f"🎓 Matrícula realizada com sucesso nos cursos: {cursos_ids}")

    mensagem = (
        f"Oii {nome}, Seja bem Vindo/a Ao CED BRASIL\n\n"
        "*Seu acesso:*\n"
        f"Login: *{cpf}*\n"
        "Senha: *123456*\n\n"
        "🌐 *Portal do aluno:* https://ead.cedbrasilia.com.br\n"
        "📲 *App Android:* https://play.google.com/store/apps/details?id=br.com.om.app&hl=pt_BR\n"
        "📱 *App iOS:* https://apps.apple.com/br/app/meu-app-de-cursos/id1581898914\n\n"
        f"📞 *Suporte:* {SUPORTE_WHATSAPP}"
    )

    numero_whatsapp = "55" + ''.join(filter(str.isdigit, celular))[-11:]
    print(f"📤 Enviando mensagem via ChatPro para {numero_whatsapp}")
    resp_whatsapp = requests.post(
        CHATPRO_URL,
        json={
            "number": numero_whatsapp,
            "message": mensagem
        },
        headers={
            "Authorization": CHATPRO_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    )

    if resp_whatsapp.status_code != 200:
        print("❌ Erro ao enviar WhatsApp:", resp_whatsapp.text)
    else:
        print("✅ Mensagem enviada com sucesso")

    return jsonify({
        "message": "Aluno cadastrado, matriculado e notificado com sucesso!",
        "aluno_id": aluno_id,
        "cursos": cursos_ids
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
