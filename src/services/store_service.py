import os
import uuid

import openai
import requests
from bson.objectid import ObjectId
from pymongo import MongoClient

from models import Chunk

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY


class MongoDBDocumentStore:
    def __init__(self, uri: str, db_name: str, collection_name: str):
        self.client = MongoClient(uri)
        self.collection = self.client[db_name][collection_name]

    def generate_embedding(self, text: str):
        """Generate embeddings using OpenAI API for a given text."""
        response = openai.embeddings.create(
            input=[text], model="text-embedding-3-small"
        )
        return response.data[0].embedding

    def add_document(self, text: str, metadata: dict):
        """Store a single document chunk with embedding in MongoDB."""
        doc_id = uuid.uuid4().hex
        embedding = self.generate_embedding(text)
        self.collection.insert_one(
            {
                "_id": doc_id,
                "text": text,
                "metadata": metadata,
                "embedding": embedding,
            }
        )
        return doc_id

    def get_doc_chunks(self, doc_id: str, page_num: int = None) -> list[dict]:
        query_dict = {"metadata.docId": ObjectId(doc_id)}
        if page_num is not None:
            query_dict["metadata.pageNum"] = page_num

        result = self.collection.find(query_dict)
        return list(result)

    def vector_search(self, allowed_doc_ids: list[str], query_text: str, limit=5):
        query_embedding = self.generate_embedding(query_text)

        result = self.collection.aggregate(
            [
                {
                    "$vectorSearch": {
                        "filter": {
                            "metadata.docId": {
                                "$in": [ObjectId(_id) for _id in allowed_doc_ids]
                            },
                        },
                        "index": "vector-index",
                        "path": "embedding",
                        "queryVector": query_embedding,
                        "numCandidates": 50,
                        "limit": limit,
                    }
                },
                {
                    "$addFields": {
                        "similarityScore": {
                            "$meta": "searchScore",
                        },
                    },
                },
                {
                    "$sort": {
                        "similarityScore": -1,
                    },
                },
            ]
        )

        return list(result)
