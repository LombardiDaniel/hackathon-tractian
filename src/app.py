import os
from collections import OrderedDict
from uuid import uuid4

import openai
from flask import Flask, jsonify, request
from flask_cors import CORS

from main import (
    formatar_resultado,
    genprompt,
    remove_duplicates_ordered,
    remove_negative_values,
)
from services import MongoDBDocumentStore

app = Flask(__name__)
# CORS(
#     app,
#     resources={
#         r"/*": {
#             "origins": "*",
#             "allow_headers": "*",
#             "expose_headers": "*",
#             "allow_methods": "*",
#         }
#     },
# )
cors = CORS(app)
# app.config["CORS_HEADERS"] = "Content-Type"
MONGODB_ATLAS_CLUSTER_URI = os.getenv("MONGODB_ATLAS_CLUSTER_URI")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

DB_NAME = "hackathon-tractian"
COLLECTION_NAME = "hackathon-tractian-vectorstores"


STORE_SERVICE = MongoDBDocumentStore(
    MONGODB_ATLAS_CLUSTER_URI, DB_NAME, COLLECTION_NAME
)

NR12_ID = "671fc44758dc9867a50d752a"
W22_ID = "671fa85458dc9867a50d751e"

asked = []
# {
#     "message": ""
# }
# {
#     "reply": "STRING",
# }


# @cross_origin()
@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data["message"]

    results: list[dict] = STORE_SERVICE.vector_search([NR12_ID], question)
    pages: list[int] = []
    for res in results:
        page_num = res["metadata"]["pageNum"]
        docId = res["metadata"]["docId"]
        text = res["text"]
        # search_results.append(formatar_resultado(page_num, docId, text))
        pages.append(page_num - 1)
        pages.append(page_num)
        pages.append(page_num + 1)

    pages = remove_duplicates_ordered(pages)
    pages = remove_negative_values(pages)

    chunks = []
    for page in pages:
        chunks.extend(STORE_SERVICE.get_doc_chunks(NR12_ID, page))

    search_results: list[str] = []
    for chunk in chunks:
        # print(chunk["text"])
        page_num = chunk["metadata"]["pageNum"]
        docId = chunk["metadata"]["docId"]
        text = chunk["text"]
        search_results.append(formatar_resultado(page_num, docId, text))

    system_prompt = genprompt(["segurança no trabalho"], search_results)

    asked.append(
        {"role": "user", "content": question},
    )
    messages = [_ for _ in asked]
    if len(asked) >= 10:
        asked = asked[-10:]

    messages.append({"role": "system", "content": system_prompt})

    # print(messages)

    reply = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )
    rep_string = reply.choices[0].message.content
    asked.append(
        {"role": "assistant", "content": rep_string},
    )

    return jsonify({"reply": rep_string})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5555, debug=True)
