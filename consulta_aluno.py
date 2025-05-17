import requests

OURO_BASE_URL = "https://meuappdecursos.com.br/ws/v2"
BASIC_AUTH = "ZTZmYzU4MzUxMWIxYjg4YzM0YmQyYTI2MTAyNDhhOGM6"

def consultar_aluno_por_cpf(cpf):
    """
    Consulta o ID do aluno com base no CPF fornecido.

    Args:
        cpf (str): CPF do aluno (apenas números).

    Returns:
        dict: Dados do aluno, incluindo o ID, ou None se não encontrado.
    """
    try:
        response = requests.get(
            f"{OURO_BASE_URL}/alunos",
            headers={"Authorization": f"Basic {BASIC_AUTH}"},
            params={"cpf": cpf}
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "true" and data.get("data"):
                return data["data"][0]  # Retorna o primeiro aluno encontrado
            else:
                print(f"⚠️ Nenhum aluno encontrado para o CPF: {cpf}")
        else:
            print(f"❌ Erro na consulta: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Exceção ao consultar aluno: {str(e)}")

    return None

# Exemplo de uso
if __name__ == "__main__":
    cpf = "12345678900"  # Substitua pelo CPF desejado
    aluno = consultar_aluno_por_cpf(cpf)
    if aluno:
        print(f"Aluno encontrado: {aluno}")
    else:
        print("Aluno não encontrado.")
