import os
import google.generativeai as genai
import json 

# Configura a API usando a chave do arquivo .env
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    print(f"Erro ao configurar a API do Gemini. Verifique sua API_KEY: {e}")

# Configurações do modelo de IA
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    generation_config=generation_config,
    safety_settings=safety_settings
)

def generate_insights_and_title(original_content):
    """
    Envia o conteúdo para a API do Gemini e retorna um título e os insights,
    limpando a formatação Markdown da resposta.
    """
    if not os.getenv("GEMINI_API_KEY"):
        return {"error": "A chave da API do Gemini não foi configurada."}

    raw_response_text = "" # Inicializa a variável para o caso de erro na API
    try:
        # ... (código do prompt continua o mesmo) ...
        prompt = f"""
        Você é um assistente criativo. Analise a seguinte ideia de um usuário e retorne um objeto JSON.
        A ideia é:
        ---
        {original_content}
        ---
        Sua tarefa é gerar:
        1. Um título curto e conciso para esta ideia (no máximo 5 palavras).
        2. Insights sobre a ideia, formatados em Markdown.

        Responda APENAS com um objeto JSON válido com a seguinte estrutura:
        {{
          "title": "Seu Título Gerado Aqui",
          "insights_markdown": "Seus insights formatados em **Markdown** aqui."
        }}
        """
        
        response = model.generate_content(prompt)
        raw_response_text = response.text

        # --- NOVA ETAPA DE LIMPEZA ---
        # Remove o bloco de código Markdown e espaços em branco extras
        cleaned_text = raw_response_text.strip().replace("```json", "").replace("```", "").strip()
        # -----------------------------
        
        # Agora usamos o texto limpo para o parse
        result = json.loads(cleaned_text)
        return result

    except Exception as e:
        print(f"Ocorreu um erro na API ou no parsing do JSON: {e}")
        # Imprime o texto que causou o erro para facilitar a depuração
        print(f"Texto recebido que causou o erro: {raw_response_text}")
        return {"error": f"Ocorreu um erro ao processar a ideia. Detalhes: {e}"}
