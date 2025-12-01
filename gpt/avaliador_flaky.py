import os
import zipfile
import json
import shutil
import random
import time
import sys
import openai
from openai import OpenAI

# --- CONFIGURAÇÕES ---
API_KEY = ""
# Diretório para testes FLAKY (existente)
FLAKY_DIR = "./flaky" 
# Diretório para testes NÃO-FLAKY (existente)
NON_FLAKY_DIR = "./nao-flaky"
# Diretório temporário (para extrair zip, se necessário)
TEMP_DIR = "./temp_dataset" 

DELAY_ENTRE_REQUESTS = 6

try:
    client = OpenAI(api_key=API_KEY)
except Exception as e:
    print(f"Erro ao inicializar o cliente OpenAI: {e}")
    sys.exit(1)


# 💡 MODELO OPENAI
# OPENAI_MODEL = "gpt-3.5-turbo" 
# OPENAI_MODEL = "gpt-4o-mini" 
OPENAI_MODEL = "gpt-4o" 

# O prompt do sistema
SYSTEM_PROMPT = """
Você é um Engenheiro de QA Sênior especialista em iOS e Swift.
Sua tarefa é analisar o código de um Teste Unitário ou UI Test e classificar se ele é FLAKY (intermitente) ou NÃO.

Sinais de alerta para Flakiness:
1. Uso de `sleep()`, `Thread.sleep`, `asyncAfter` com tempos fixos.
2. Chamadas de rede reais (URLSession) sem uso de Mocks/Stubs.
3. Dependência de Data/Hora do sistema (`Date()`, `Date.now`) sem injeção.
4. Uso de números aleatórios (`Int.random`) sem semente fixa.
5. Testes de UI dependendo de animações sem expectativas (wait/expectations).
6. Race conditions (concorrência sem proteção).

IMPORTANTE:
Sempre que eu enviar um código, analise e responda APENAS um objeto JSON com este formato exato:
{
  "is_flaky": true/false,
  "confidence": "High" ou "Low",
  "reason": "Explicação técnica sucinta em 1 frase."
}
"""

def descompactar_zip(zip_path, pasta_destino):
    """Apenas descompacta o arquivo zip."""
    if not os.path.exists(zip_path):
        print(f"⚠️ Aviso: Zip não encontrado: {zip_path}")
        return False
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(pasta_destino)
        return True
    except Exception as e:
        print(f"Erro ao extrair {zip_path}: {e}")
        return False

def listar_arquivos_swift(diretorio_base):
    """Varre recursivamente uma pasta em busca de .swift"""
    arquivos = []
    if not os.path.exists(diretorio_base):
        return []
    
    for root, dirs, files in os.walk(diretorio_base):
        for file in files:
            if file.endswith(".swift"):
                arquivos.append(os.path.join(root, file))
    return arquivos

def analisar_com_chat(codigo_swift):
    """Chama a API da OpenAI para análise, usando o cliente global."""
    
    # Prepara a lista de mensagens para a chamada
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Analise este código:\n\n```swift\n{codigo_swift}\n```"}
    ]
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            # Força a resposta a ser JSON
            response_format={"type": "json_object"} 
        )
        
        # O objeto JSON é retornado diretamente como uma string no campo 'content'
        json_string = response.choices[0].message.content
        return json.loads(json_string)
        
    except openai.APIError as e:
        # Erros específicos da API da OpenAI
        print(f"Erro da API da OpenAI: {e}")
        return {"is_flaky": False, "error": True, "error_msg": str(e)}
    except Exception as e:
        # Erros de parsing JSON ou outros erros
        print(f"Erro de processamento/JSON: {e}")
        return {"is_flaky": False, "error": True, "error_msg": str(e)}

def main():
    print("🚀 Iniciando Pipeline (Pasta Local + Zip) com OpenAI API...")
    
    # Limpa apenas o temp 
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)

    # --- 1. PREPARAÇÃO DAS LISTAS DE ARQUIVOS ---
    
    # A) FLAKY: Ler direto da pasta local
    print(f"📂 Lendo arquivos flaky de: {FLAKY_DIR}")
    lista_flaky = listar_arquivos_swift(FLAKY_DIR)
    
    # B) NÃO-FLAKY: Lê da pasta local. Se o NON_FLAKY_DIR for um zip, você 
    # precisará descompactá-lo manualmente no TEMP_DIR e listar a partir daí.
    # Assumindo que NON_FLAKY_DIR é um diretório, como FLAKY_DIR.
    print(f"📂 Lendo arquivos clean de: {NON_FLAKY_DIR}")
    lista_nao_flaky = listar_arquivos_swift(NON_FLAKY_DIR)
    
    print("-" * 40)
    print(f"📄 Total Flaky (Pasta):  {len(lista_flaky)}")
    print(f"📄 Total Clean (Pasta):  {len(lista_nao_flaky)}")
    print("-" * 40)

    # --- 2. SELEÇÃO E SHUFFLE ---
    target_count = min(len(lista_flaky), len(lista_nao_flaky))
    
    if target_count == 0:
        print("❌ Erro: Não há arquivos suficientes (verifique se as pastas/zips existem).")
        return

    print(f"⚖️  Selecionando {target_count} arquivos aleatórios de cada grupo.")
    
    amostra_flaky = random.sample(lista_flaky, target_count)
    amostra_nao_flaky = random.sample(lista_nao_flaky, target_count)
    
    dataset = []
    for f in amostra_flaky:
        dataset.append((f, True))   # True = É Flaky
    for f in amostra_nao_flaky:
        dataset.append((f, False))  # False = Não é Flaky
        
    random.shuffle(dataset)
    print("🔀 Dataset embaralhado.")

    # --- 3. EXECUÇÃO ---
    resultados = {"TP": 0, "TN": 0, "FP": 0, "FN": 0, "Errors": 0}
    total_arquivos = len(dataset)
    start_time = time.time()

    print(f"\n🕵️  PROCESSANDO (Delay {DELAY_ENTRE_REQUESTS}s)...\n")

    for i, (caminho, is_realmente_flaky) in enumerate(dataset):
        nome_arq = os.path.basename(caminho)
        
        try:
            with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                codigo = f.read()
            
            # Chama a LLM
            predicao = analisar_com_chat(codigo)
            
            if predicao.get("error"):
                print(f"[{i+1}/{total_arquivos}] ⚠️ ERRO API | {nome_arq} | {predicao.get('error_msg', 'Erro desconhecido')}")
                resultados["Errors"] += 1
                time.sleep(DELAY_ENTRE_REQUESTS)
                continue

            llm_disse_flaky = predicao.get("is_flaky", False)
            reason = predicao.get("reason", "Sem motivo")
            
            acertou = (llm_disse_flaky == is_realmente_flaky)
            
            # Log e contagem
            if is_realmente_flaky and llm_disse_flaky:
                resultados["TP"] += 1
                status_emoji = "✅ TP (Era Flaky -> Disse Flaky)"
            elif not is_realmente_flaky and not llm_disse_flaky:
                resultados["TN"] += 1
                status_emoji = "✅ TN (Era Clean -> Disse Clean)"
            elif not is_realmente_flaky and llm_disse_flaky:
                resultados["FP"] += 1
                status_emoji = "❌ FP (Era Clean -> Disse Flaky)"
            elif is_realmente_flaky and not llm_disse_flaky:
                resultados["FN"] += 1
                status_emoji = "❌ FN (Era Flaky -> Disse Clean)"

            print(f"[{i+1}/{total_arquivos}] {status_emoji}")
            print(f"   └── Arq: {nome_arq}")
            print(f"   └── Motivo: {reason}")
            
            time.sleep(DELAY_ENTRE_REQUESTS)

        except Exception as e:
            print(f"Erro fatal no loop: {e}")
            resultados["Errors"] += 1

    # Cálculo do Relatório
    total_validos = len(dataset) - resultados["Errors"]
    acuracia = ((resultados["TP"] + resultados["TN"]) / total_validos * 100) if total_validos > 0 else 0
    precision = (resultados["TP"] / (resultados["TP"] + resultados["FP"]) * 100) if (resultados["TP"] + resultados["FP"]) > 0 else 0
    recall = (resultados["TP"] / (resultados["TP"] + resultados["FN"]) * 100) if (resultados["TP"] + resultados["FN"]) > 0 else 0
    f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    print("\n" + "="*50)
    print(f"📊 RESULTADO FINAL")
    print(f"Acurácia: {acuracia:.2f}% | F1-Score: {f1_score:.2f}%")
    print(f"TP: {resultados['TP']} | TN: {resultados['TN']} | FP: {resultados['FP']} | FN: {resultados['FN']}")
    print("="*50)

    # Limpa o diretório temporário
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
        print(f"Cleanup: Diretório temporário {TEMP_DIR} removido.")

if __name__ == "__main__":
    main()