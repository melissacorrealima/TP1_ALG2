# Trabalho Prático 1 - Indexação Geoespacial e Geometria Computacional Híbrida

Nesse trabalho foram abordados os aspectos práticos da integração entre estruturas de dados para tratamento de strings e algoritmos de geometria computacional, através da implementação de árvores de prefixos aplicadas à codificação Geohash.

## Tecnologias Utilizadas
- Python
- Pandas
- Folium
- Streamlit

## Como Rodar
Execute no terminal as etapas a seguir na pasta raíz do projeto:
1. Crie um novo ambiente virtual
- Linux, macOS ou Git Bash:
```
python3 -m venv .venv
```
- Windows (PowerShell):
```
python -m venv .venv
```
2. Ative o ambiente virtual
- Linux, macOS ou Git Bash:
```
source .venv/bin/activate
```
- Windows (PowerShell):
```
.venv\Scripts\Activate.ps1
```
3. Instale as dependências de `requirements.txt`
```
pip install -r requirements.txt
python.exe -m pip install --upgrade pip  // caso alguma atualização seja necessária
```
4. Executar a aplicação Streamlit
```
python -m streamlit run app.py
```
- O terminal exibirá o endereço de acesso: `http://localhost:8501`
- O navegador abrirá automaticamente a página com a aplicação do trabalho.
- Para interromper a aplicação pressione `Ctrl + C` no terminal onde o Streamlit está rodando para encerrar o servidor local.
