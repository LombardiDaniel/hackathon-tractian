import requests

r = requests.post(
    "http://localhost:5555/ask",
    json={"message": "como funciona a segurança das prensas?"},
)

print(r.content)
