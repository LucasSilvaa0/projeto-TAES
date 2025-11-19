from dotenv import load_dotenv
import os
import requests
import sys
import json

load_dotenv()

def consultar_deepseek_local(codigo_teste):
    url = "http://localhost:11434/api/generate"
    
    prompt = f"""Analise este código de teste para identificar possíveis causas de flaky tests:

                {codigo_teste}

                Procure por:
                1. Race conditions
                2. Dependência de estado compartilhado
                3. Problemas com async/await
                4. Uso de timestamps ou delays
                5. Mocks não determinísticos
                6. Ordem de execução problemática

                Retorne um JSON com as suspeitas encontradas."""

    modelos = [
        "deepseek-coder:1.3b",
        "codellama:7b",
        "llama2:7b", 
        "deepseek-coder:6.7b" 
    ]
    
    for modelo in modelos:
        try:
            print(f"🔍 Tentando modelo: {modelo}", file=sys.stderr)
            
            data = {
                "model": modelo,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 800,
                    "temperature": 0.1
                }
            }
            
            response = requests.post(url, json=data, timeout=90)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Sucesso com modelo: {modelo}", file=sys.stderr)
                return result["response"]
            else:
                print(f"❌ Modelo {modelo} falhou: {response.status_code}", file=sys.stderr)
                continue
                
        except Exception as e:
            print(f"❌ Erro com {modelo}: {e}", file=sys.stderr)
            continue
    
    return '{"erro": "Todos os modelos falharam por falta de memória. Tente usar um modelo menor."}'

if __name__ == "__main__":
    codigo = sys.stdin.read()
    if not codigo.strip():
        print('{"erro": "Nenhum código fornecido"}')
        sys.exit(1)
    
    resultado = consultar_deepseek_local(codigo)
    print(resultado)