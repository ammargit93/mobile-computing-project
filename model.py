from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os

load_dotenv()
client = InferenceClient(
	provider="hf-inference",
	api_key=os.getenv('HF_TOKEN')
)

def chat_with_bot(user_input):
    messages = [
        {
            "role": "user",
            "content": user_input
        }
    ]

    completion = client.chat.completions.create(
        model="google/gemma-2-2b-it", 
        messages=messages, 
        max_tokens=500
    )

    print(completion.choices[0].message.content)
    return completion.choices[0].message.content