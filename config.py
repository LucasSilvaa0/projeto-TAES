from dotenv import load_dotenv
import os
import requests
import sys

load_dotenv()

API_KEY_DEEPSEEK = os.getenv("API_KEY")

def consultar_deepseek(codigo_teste):
    API_KEY_DEEPSEEK = os.getenv("API_KEY")
    url = "https://api.deepseek.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {API_KEY_DEEPSEEK}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    Analise este código de teste para identificar possíveis causas de flaky tests:
    
    {codigo_teste}
    
    Procure por:
    1. Race conditions
    2. Dependência de estado compartilhado
    3. Problemas com async/await
    4. Uso de timestamps ou delays
    5. Mocks não determinísticos
    6. Ordem de execução problemática
    
    Retorne um JSON com as suspeitas encontradas.
    """
    
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()["choices"][0]["message"]["content"]

if __name__ == "__main__":
    codigo = sys.stdin.read()
    resultado = consultar_deepseek(codigo)
    print(resultado)