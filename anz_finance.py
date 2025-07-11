from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from datetime import datetime
from tqdm import tqdm
import pandas as pd
import ofxparse
import os

_ = load_dotenv(find_dotenv())

# ========================= OFX Parsing =========================
df = pd.DataFrame()
for extrato in os.listdir("extratos"):
    try:
        with open(f"extratos/{extrato}", "rb") as ofx_file:
            ofx = ofxparse.OfxParser.parse(ofx_file)

        transactions_data = []
        for account in ofx.accounts:
            for transaction in account.statement.transactions:
                transactions_data.append({
                    "Data": transaction.date,
                    "Valor": transaction.amount,
                    "Descrição": transaction.memo,
                    "ID": transaction.id, 
                })
            
        df_temp = pd.DataFrame(transactions_data)
        if not df_temp.empty:
            df_temp["Valor"] = df_temp["Valor"].astype(float)
            df_temp["Data"] = df_temp["Data"].apply(lambda x: x.date())
            df = pd.concat([df, df_temp], ignore_index=True)
        else:
            print(f"[DEBUG] No transactions in: {extrato}")
    except Exception as e:
        print(f"[ERROR] Failed to process {extrato}: {e}")

# ========================= Prompt =========================

template = """
Você é um assistente especializado em análise de finanças pessoais.
Seu papel é **classificar transações financeiras** com base em sua descrição, valor e data.

Cada transação representa um gasto ou receita real feito por uma pessoa física, como você ou eu.

Escolha a **categoria mais adequada** para cada transação analisando o contexto do texto (descrição), 
o valor e, se necessário, o padrão comum de comportamento financeiro.

Considere os seguintes grupos de categorias disponíveis:

🏠 Moradia → Aluguel, condomínio, contas de luz/água/gás, manutenção da casa  
🍞 Alimentação → Restaurantes, cafés, delivery, padaria, lanches  
🛒 Mercado → Supermercado, açougue, hortifruti, compras mensais  
🚗 Transporte → Gasolina, Uber, ônibus, manutenção de carro ou moto  
💡 Telefone → Plano de celular, internet, recarga  
💰 Receitas → Salários, depósitos, transferências recebidas  
💸 Transferência para terceiros → Envio de dinheiro para amigos, familiares, Pix  
🧾 Compras → Eletrodomésticos, eletrônicos, roupas, itens de uso pessoal  
📚 Educação → Mensalidades, cursos online, livros, materiais escolares  
🏥 Saúde → Farmácia, exames, planos de saúde, médicos  
📈 Investimento → Aporte em corretoras, fundos, Tesouro Direto, ações  

Responda apenas com uma das categorias acima (exatamente como está escrita), sem explicações.

Agora, classifique a seguinte transação:
{text}
"""

prompt = PromptTemplate.from_template(template=template)

# ========================= LLMs =========================
chat = ChatGroq(
    model="llama3-8b-8192",
    api_key=os.getenv("GROQ_API_KEY")
)

chain = prompt | chat

print("Sorting transactions one by one...")

categorias = []
for descricao in tqdm(df["Descrição"].values, desc="Sorting"):
    try:
        resposta = chain.invoke(descricao).content
    except Exception as e:
        print(f"[ERROR] when sorting: {descricao} -> {e}")
        resposta = "Error"
    categorias.append(resposta)

df["Categorias"] = categorias
df.to_csv("finances.csv", index=False)
print("✅ Successfully generated 'finances.csv' file!")

