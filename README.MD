# Avaliador de _flakiness_ com LLM

## Como executar:
- Descompacte os arquivos `flaky.zip` e `nao-flaky.zip`
    - **Mantenha a estrutura das pastas**
- Mova as pastas geradas pelo passo anterior para a pasta correspondente à LLM que deseja testar
- Deepseek
    - Configure as constantes `API_KEY` `URL`
- Gemini
    - Configure a constante `API_KEY`
- GPT
    - Configure as constante `API_KEY` e `OPENAI_MODEL`
- Llama
    - passos especificos aqui
- Execute o arquivo `avaliador_flaky.py`