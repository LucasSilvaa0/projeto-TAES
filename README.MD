# Avaliador de _flakiness_ com LLM

## Como executar:
- Descompacte os arquivos `flaky.zip` e `nao-flaky.zip`
    - **Mantenha a estrutura das pastas**
- Mova as pastas geradas pelo passo anterior para a pasta correspondente à LLM que deseja testar
- Deepseek
    - Instale a LLM localmente e configure a `URL`
- Gemini
    - Configure a constante `API_KEY`
- GPT
    - Configure as constante `API_KEY` e `OPENAI_MODEL`
- Llama
    - Instale a LLM localmente e ...
- Execute o arquivo `avaliador_flaky.py`
