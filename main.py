from flask import Flask, request, jsonify
import requests
from requests.auth import HTTPBasicAuth
import datetime
import os
from consulta_aluno import consultar_aluno_por_cpf

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
    "Example plan": [161, 201],
    "Operador de micro/Maria": [130, 599, 163, 160, 161, 162, 222]
}

API_URL = "https://meuappdecursos.com.br/ws/v2/unidades/token/"
ID_UNIDADE = 4158
KEY = "e6fc583511b1b88c34bd2a2610248a8c"

TOKEN_UNIDADE = None

def enviar_log_whatsapp(mensagem):
    try:
        msg_formatada = requests.utils.quote(mensagem)
        url = f"https://api.callmebot.com/whatsapp.php?phone={CALLMEBOT_PHONE}&text={msg_formatada}&apikey={CALLMEBOT_APIKEY}"
        resp = requests.get(url)
        if resp.status_code == 200:
            print("✅ Log enviado ao WhatsApp com sucesso.")
        else:
            print("❌ Falha ao enviar log para WhatsApp:", resp.text)
    except Exception as e:
        print("❌ Erro ao enviar log para WhatsApp:", str(e))

def obter_token_unidade():
    global TOKEN_UNIDADE
    try:
        resposta = requests.get(API_URL + f"{ID_UNIDADE}", auth=HTTPBasicAuth(KEY, ""))
        dados = resposta.json()
        if dados.get("status") == "true":
            TOKEN_UNIDADE = dados.get("data")["token"]
            print("🔁 Token atualizado com sucesso!")
            return TOKEN_UNIDADE
        print("❌ Erro ao obter token:", dados)
        enviar_log_whatsapp(f"❌ Erro ao obter token da unidade: {dados}")
    except Exception as e:
        print("❌ Exceção ao obter token:", str(e))
        enviar_log_whatsapp(f"❌ Exceção ao obter token: {str(e)}")
    return None

# Inicializa o token ao iniciar o app
obter_token_unidade()

@app.before_request
def log_request_info():
    print("\n📥 Requisição recebida:")
    print("🔗 URL completa:", request.url)
    print("📍 Método:", request.method)
    print("📦 Cabeçalhos:", dict(request.headers))

@app.route('/secure', methods=['GET', 'HEAD'])
def secure_check():
    obter_token_unidade()
    return "🔐 Token atualizado com sucesso via /secure", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        print("\n🔔 Webhook recebido com sucesso")
        payload = request.json
        evento = payload.get("webhook_event_type")

        if evento == "order_approved":
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
                erro_msg = f"❌ ERRO NO CADASTRO: {resp_cadastro.text}\nAluno: {nome}, CPF: {cpf}, Email: {email}, Celular: {celular}"
                print(erro_msg)
                enviar_log_whatsapp(erro_msg)
                return jsonify({"error": "Falha ao criar aluno", "detalhes": resp_cadastro.text}), 500

            aluno_id = aluno_response.get("data", {}).get("id")
            if not aluno_id:
                erro_msg = f"❌ ID do aluno não retornado!\nAluno: {nome}, CPF: {cpf}, Celular: {celular}"
                print(erro_msg)
                enviar_log_whatsapp(erro_msg)
                return jsonify({"error": "ID do aluno não encontrado na resposta de cadastro."}), 500

            print(f"✅ Aluno criado com sucesso. ID: {aluno_id}")

            # Store aluno_id for later use (e.g., deletion during refund)
            # This could be a database or in-memory storage, depending on the system design
            # For now, we assume a simple in-memory dictionary (global variable)
            global ALUNOS_CACHE
            if 'ALUNOS_CACHE' not in globals():
                ALUNOS_CACHE = {}
            ALUNOS_CACHE[cpf] = aluno_id

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
                erro_msg = (
                    f"❌ ERRO NA MATRÍCULA\n"
                    f"Aluno ID: {aluno_id}\n"
                    f"👤 Nome: {nome}\n"
                    f"📄 CPF: {cpf}\n"
                    f"📱 Celular: {celular}\n"
                    f"🎓 Cursos: {cursos_ids}\n"
                    f"🔧 Detalhes: {resp_matricula.text}"
                )
                print(erro_msg)
                enviar_log_whatsapp(erro_msg)
                return jsonify({"error": "Falha ao matricular", "detalhes": resp_matricula.text}), 500

            msg_matricula = (
                f"✅ MATRÍCULA REALIZADA COM SUCESSO\n"
                f"👤 Nome: {nome}\n"
                f"📄 CPF: {cpf}\n"
                f"📱 Celular: {celular}\n"
                f"🎓 Cursos: {cursos_ids}\n"
                f"🆔 ID do Aluno: {aluno_id}"
            )
            print(msg_matricula)
            enviar_log_whatsapp(msg_matricula)

            mensagem = (
                f"Oii {nome}, Seja bem Vindo/a Ao CED BRASIL\n\n"
                f"📦 *Plano adquirido:* {plano_assinatura}\n\n"
                "*Seu acesso:*\n"
                f"Login: *{cpf}*\n"
                "Senha: *123456*\n\n"
                "🌐 *Portal do aluno:* https://ead.cedbrasilia.com.br\n"
                "📲 *App Android:* https://play.google.com/store/apps/details?id=br.com.om.app&hl=pt_BR\n"
                "📱 *App iOS:* https://apps.apple.com/br/app/meu-app-de-cursos/id1581898914\n\n"
                f"🆔 *ID do Aluno:* {aluno_id}\n"
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
                "message": "Aluno cadastrado, matriculado e notificado com sucesso! Matrícula efetuada com sucesso!",
                "aluno_id": aluno_id,
                "cursos": cursos_ids
            }), 200

        elif evento == "order_refunded":
            # Extração do CPF do cliente
            cpf = payload.get("order", {}).get("Customer", {}).get("CPF")
            if not cpf:
                print("❌ CPF do cliente não fornecido para o evento de reembolso.")
                return jsonify({"error": "CPF do cliente não fornecido para o evento de reembolso."}), 400

            print(f"🔄 Processando reembolso para o CPF do cliente: {cpf}")

            # Consultar o ID do aluno com base no CPF
            aluno = consultar_aluno_por_cpf(cpf)
            if not aluno or not aluno.get("id"):
                erro_msg = f"❌ ID do aluno não encontrado para o CPF: {cpf}"
                print(erro_msg)
                enviar_log_whatsapp(erro_msg)
                return jsonify({"error": "ID do aluno não encontrado."}), 400

            aluno_id = aluno["id"]

            # Enviar requisição para deletar a conta do aluno
            try:
                resp_deletar = requests.delete(
                    f"{OURO_BASE_URL}/alunos/{aluno_id}",
                    headers={"Authorization": f"Basic {BASIC_AUTH}"}
                )

                if not resp_deletar.ok:
                    erro_msg = f"❌ ERRO AO DELETAR CONTA: {resp_deletar.text}\nID do aluno: {aluno_id}"
                    print(erro_msg)
                    enviar_log_whatsapp(erro_msg)
                    return jsonify({"error": "Falha ao deletar conta do aluno", "detalhes": resp_deletar.text}), 500

                print(f"✅ Conta do aluno com ID {aluno_id} deletada com sucesso.")
                return jsonify({"message": "Conta do aluno deletada com sucesso."}), 200

            except Exception as e:
                erro_msg = f"❌ EXCEÇÃO AO DELETAR CONTA: {str(e)}\nID do aluno: {aluno_id}"
                print(erro_msg)
                enviar_log_whatsapp(erro_msg)
                return jsonify({"error": "Erro interno ao deletar conta", "detalhes": str(e)}), 500

        else:
            # Ignorar outros eventos
            print(f"🔕 Evento ignorado: {evento}")
            return jsonify({"message": "Evento ignorado"}), 200

    except Exception as e:
        erro_msg = f"❌ EXCEÇÃO NO PROCESSAMENTO: {str(e)}"
        print(erro_msg)
        enviar_log_whatsapp(erro_msg)
        return jsonify({"error": "Erro interno no servidor", "detalhes": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
