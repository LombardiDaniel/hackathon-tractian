import os
import time
from io import BytesIO
from uuid import uuid4

from bson.objectid import ObjectId
from langchain_core.documents import Document
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from tqdm import tqdm

from models import Chunk
from services import MongoDBDocumentStore, PDFService

# Set up environment variables
MONGODB_ATLAS_CLUSTER_URI = os.getenv("MONGODB_ATLAS_CLUSTER_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = MongoClient(MONGODB_ATLAS_CLUSTER_URI)

DB_NAME = "hackathon-tractian"
COLLECTION_NAME = "hackathon-tractian-vectorstores"

store_service = MongoDBDocumentStore(
    MONGODB_ATLAS_CLUSTER_URI, DB_NAME, COLLECTION_NAME
)

pdf_buffer: BytesIO = None
with open("../NR12.pdf", "rb") as file:
    pdf_buffer = BytesIO(file.read())

pdf_pages = PDFService.pdf_to_text(pdf_buffer)

chunks = PDFService.text_to_chunks(pdf_pages)
for chunk in tqdm(chunks):
    # print(chunk.text)
    # time.sleep(0.1)
    store_service.add_document(
        chunk.text,
        {
            "docId": ObjectId("671fc44758dc9867a50d752a"),
            "pageNum": chunk.page_num,
        },
    )
    # break
