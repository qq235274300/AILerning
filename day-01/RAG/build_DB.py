from pathlib import Path

from RAG.pdfLoader import pdf_to_images
from RAG.ocr import image_to_documents
from RAG.DBchunk import split_documents
from RAG.DBembedding import get_document_embeddings
from RAG.chroma import ChromaDB

pdf_path = Path(__file__).parent / "虚幻引擎程序设计浅析.pdf"


images = pdf_to_images(pdf_path)


documents  = image_to_documents(images, source=pdf_path.name)


chunks = split_documents(documents)


embeddings = get_document_embeddings(chunks)


db = ChromaDB()


db.add(
    chunks,
    embeddings
)


print("知识库建立完成")
