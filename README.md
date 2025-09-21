# ANZ Finance

Projeto para analisar extratos bancários no formato OFX, classificar automaticamente as transações financeiras usando modelos LLM (Groq AI) e apresentar um dashboard interativo com filtros para visualização dos dados.

---

## Funcionalidades

- Processa extratos OFX de múltiplos arquivos, extraindo dados de transações (data, valor, descrição, id).
- Usa um modelo de linguagem (Groq AI) para classificar cada transação em categorias financeiras pré-definidas.
- Gera um arquivo `finances.csv` com as transações classificadas.
- Dashboard web interativo feito com Streamlit para explorar e filtrar os dados, com tabelas e gráficos de pizza.

---

## Estrutura do Projeto

```bash
anz_finance/
├── modules/
│ ├── parsers/
│ │ └── ofx_parser.py   # Funções para leitura e parsing de arquivos OFX
│ ├── llm/
│ │ └── categorizer.py  # Classificação das transações usando Groq LLM
│ ├── data/
│ │ └── finance_data.py # Tratamento, filtragem e manipulação dos dados financeiros
│ └── dashboard/
│ └── streamlit_app.py  # Código do dashboard Streamlit (interface)
│
├── generate_csv.py     # Script principal para gerar o arquivo CSV a partir dos extratos e classificação
├── run_dashboard.py    # Script para rodar o dashboard Streamlit
├── config.py           # Configurações gerais e variáveis de ambiente
├── requirements.txt    # Dependências do projeto
└── README.md           # Este arquivo
```

---

## Tecnologias e Bibliotecas Utilizadas

- **Python 3.8+**
- [pandas](https://pandas.pydata.org/) - manipulação de dados tabulares
- [ofxparse](https://github.com/jseutter/ofxparse) - parser para arquivos OFX bancários
- [langchain](https://python.langchain.com/) e SDKs de Groq AI e OpenAI para integração com modelos de linguagem
- [tqdm](https://tqdm.github.io/) - barra de progresso para loops
- [streamlit](https://streamlit.io/) - framework para dashboard web
- [plotly](https://plotly.com/python/) - visualização gráfica interativa
- [python-dotenv](https://github.com/theskumar/python-dotenv) - para carregar variáveis de ambiente

---
