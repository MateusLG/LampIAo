import os
import json
import google.generativeai as genai

# ... (o código de configuração da API continua o mesmo) ...
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    print(f"Erro ao configurar a API do Gemini. Verifique sua API_KEY: {e}")

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
    if not os.getenv("GEMINI_API_KEY"):
        return {"error": "A chave da API do Gemini não foi configurada."}

    raw_response_text = ""
    try:
        # --- PROMPT REESTRUTURADO ---
        prompt = f"""
        # CONTEXTO
        Você é um assistente especialista em criatividade e análise de negócios. Sua função é atuar como um parceiro de brainstorming, recebendo uma ideia inicial e devolvendo uma análise estruturada para ajudar o usuário a desenvolvê-la.

        # TAREFA
        Analise a ideia fornecida pelo usuário e gere um título conciso e uma análise detalhada em formato de insights.

        # DADOS DE ENTRADA (Ideia do Usuário)
        ---
        {original_content}
        ---

        # REGRAS DE SAÍDA
        1. Sua resposta deve ser ESTRITAMENTE um objeto JSON válido, sem nenhum texto ou formatação adicional antes ou depois.
        2. O objeto JSON deve conter exatamente duas chaves: "title" e "insights_markdown".
        3. O valor de "title" deve ser uma string com no máximo 5 palavras.
        4. O valor de "insights_markdown" deve ser uma string contendo o texto formatado em Markdown, com as seguintes seções: Pontos Fortes, Possíveis Desafios e Sugestões para Aprofundamento.
        """
        
        response = model.generate_content(prompt)
        raw_response_text = response.text
        cleaned_text = raw_response_text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(cleaned_text)
        return result

    except Exception as e:
        print(f"Ocorreu um erro na API ou no parsing do JSON: {e}")
        print(f"Texto recebido que causou o erro: {raw_response_text}")
        return {"error": f"Ocorreu um erro ao processar a ideia. Detalhes: {e}"}