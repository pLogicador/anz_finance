import time
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from config import GROQ_API_KEY

prompt_template = """
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

prompt = PromptTemplate.from_template(template=prompt_template)

class Categorizer:
    DEFAULT_MODELS = ["llama-3.1-8b-instant", "llama-3.1-70b-versatile"]

    def __init__(self, model_name=None, api_key=GROQ_API_KEY):
        self.model_name = model_name or self.DEFAULT_MODELS[0]
        self.api_key = api_key
        self._init_chat(self.model_name)

    def _init_chat(self, model_name):
        try:
            self.chat = ChatGroq(model=model_name, api_key=self.api_key)
        except Exception as e:
            print(f"[WARN] Failed to initialize model {model_name}: {e}")
            fallback = self.DEFAULT_MODELS[1]
            print(f"[INFO] Trying fallback model {fallback}...")
            self.chat = ChatGroq(model=fallback, api_key=self.api_key)

    def classify(self, descriptions):
        categories = []
        for desc in descriptions:
            try:
                chain = prompt | self.chat
                res = chain.invoke(desc).content
                categories.append(res.strip())
            except Exception as e:
                print(f"[ERROR] {e}")
                categories.append("Error")
        return categories


