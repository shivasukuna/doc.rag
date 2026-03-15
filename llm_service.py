import ollama
import requests
import json

# Normal version
def generate_answer(prompt):
    response = ollama.chat(
        model="gemma2:2b",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]


def generate_answer_stream(prompt: str):

    url = "http://localhost:11434/api/generate"

    payload = {
        "model": "gemma2:2b",
        "prompt": prompt,
        "stream": True
    }

    with requests.post(url, json=payload, stream=True) as response:
        for line in response.iter_lines():
            if line:

                data = json.loads(line)

                token = data.get("response", "")
                done = data.get("done", False)

                if token:
                    yield token

                if done:
                    break