import os
from collections import OrderedDict
from uuid import uuid4

import openai

from services import MongoDBDocumentStore

MONGODB_ATLAS_CLUSTER_URI = os.getenv("MONGODB_ATLAS_CLUSTER_URI")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

DB_NAME = "hackathon-tractian"
COLLECTION_NAME = "hackathon-tractian-vectorstores"


STORE_SERVICE = MongoDBDocumentStore(
    MONGODB_ATLAS_CLUSTER_URI, DB_NAME, COLLECTION_NAME
)


def genprompt(assuntos: list[str], resultados: list[str]) -> str:
    return f"""Você é um assistente virtual que responde dúvidas de funcionários de uma empresa,
Utilizando os trechos da consulta dos documentos corporativos, responda as perguntas
do usuário corretamente. Se a resposta estiver correta, você ganhará pontos.
Inclua apenas informações encontrada nos Resultados da Pesquisa e não adicione nenhuma 
informação adicional. Tenha certeza que a resposta está correta, não responda com informações falsas.
Cite cada referência dos documentos utilizados separadamente utilizando a 
notação [id-do-arquivo numero-da-pagina] (todo resultado da pesquisa tem este número no inicio).
As referências devem ser citadas após a resposta, uma por linha. Se o assunto não se encontrar
nos resultados da pequisa, responda com "Assunto não encontrado, seja mais específico na pergunta"
Os assuntos desta conversa são: {assuntos}.\n
Resultados da Pesquisa:\n {resultados}\n"""


def formatar_resultado(page_num: int, docId: str, text: str) -> str:
    return f"[{docId} {page_num}] {text}"


def remove_duplicates_ordered(input_list):
    return list(OrderedDict.fromkeys(input_list))


def remove_negative_values(input_list):
    return [x for x in input_list if x >= 0]


NR12_ID = "671fc44758dc9867a50d752a"
W22_ID = "671fa85458dc9867a50d751e"

asked = []


def main():
    global asked
    question = "como funciona a segurança das prensas?"
    print("Chat com o manual WR22_ID:\n")
    while True:
        question = input()

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
        print(rep_string + "\n\n")


if __name__ == "__main__":
    main()
