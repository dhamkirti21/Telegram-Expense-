import os
import json
from groq import Groq
from finance_bot.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def load_prompt(filename):
    prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', filename)
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def categorize_transaction(text: str) -> dict:
    """
    Calls the Groq API to extract transaction details from text.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing. Cannot categorize transaction.")
        
    system_prompt = load_prompt('categorizer.md')
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Using a fast model for categorization
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        result_json = completion.choices[0].message.content
        return json.loads(result_json)
        
    except Exception as e:
        print(f"Error during Groq API call: {e}")
        return None

def get_financial_advice(history_json: str, user_question: str = "") -> str:
    """
    Calls the Groq API to generate financial advice based on history.
    """
    if not GROQ_API_KEY:
        return "GROQ_API_KEY is missing. Cannot generate advice."
        
    system_prompt = load_prompt('advisor.md')
    
    # Inject history into the prompt
    content = f"Here is my transaction history in JSON format:\n{history_json}\n"
    if user_question:
        content += f"\nMy specific question is: {user_question}"
        
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Or llama3-70b-8192 for better reasoning
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            temperature=0.3
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        print(f"Error during Groq API call: {e}")
        return "Sorry, I couldn't generate advice right now."
