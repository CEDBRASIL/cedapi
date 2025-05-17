import json

def enviar_log_discord(mensagem):
    webhook_url = "https://discord.com/api/webhooks/1373265105298653235/DwNCh-rD99gqJUuSnrwFW12cDEdAcn8H7SP4kucgc_He9ZZaqHNWmGO_qD_PZdf-U5Rq"
    try:
        payload = {"content": mensagem}
        headers = {"Content-Type": "application/json"}
        response = requests.post(webhook_url, data=json.dumps(payload), headers=headers)
        if response.status_code == 204:
            print("✅ Log enviado ao Discord com sucesso.")
        else:
            print(f"❌ Falha ao enviar log para Discord: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"❌ Erro ao enviar log para Discord: {str(e)}")

# Example usage in bot events
@bot.event
async def on_ready():
    mensagem = f"✅ Bot conectado como {bot.user}"
    print(mensagem)
    enviar_log_discord(mensagem)

@bot.command()
async def ping(ctx):
    mensagem = "Pong! 🏓"
    await ctx.send(mensagem)
    enviar_log_discord(mensagem)