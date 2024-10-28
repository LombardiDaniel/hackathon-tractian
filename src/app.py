import os
from uuid import uuid4

import openai
from flask import Flask, jsonify, request

from services import MongoDBDocumentStore

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
MONGODB_ATLAS_CLUSTER_URI = os.getenv(
    "MONGODB_ATLAS_CLUSTER_URI",
)

STORE_SERVICE = MongoDBDocumentStore(
    MONGODB_ATLAS_CLUSTER_URI, "hackathon-tractian", "hackathon-tractian-vectorstores"
)


@app.route("/search", methods=["POST"])
def search():
    data = request.json
    assuntos = data.get("assuntos", [])
    resultados = data.get("resultados", [])

    system_prompt = genprompt(assuntos, resultados)

    reply = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": data.get("question", ""),
            },
        ],
    )

    formatted_results = []
    for res in reply.choices[0].message.content.split("\n"):
        if res.startswith("["):
            formatted_results.append(res.strip())

    return jsonify({"results": formatted_results})


if __name__ == "__main__":
    app.run(debug=True)
