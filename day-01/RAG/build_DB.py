from pathlib import Path

from pdfLoader import pdf_to_images_limit,pdf_to_images
from ocr import image_to_text
from DBchunk import split_text
from DBembedding import get_embeddings
from chroma import ChromaDB

pdf_path = Path(__file__).parent / "虚幻引擎程序设计浅析.pdf"


images = pdf_to_images(pdf_path)


texts = image_to_text(images)


chunks = split_text(texts)


embeddings = get_embeddings(chunks)


db = ChromaDB()


db.add(
    chunks,
    embeddings
)


print("知识库建立完成")