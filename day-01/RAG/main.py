from pathlib import Path
from pdfLoader import pdf_to_images,pdf_to_images_limit
from ocr import image_to_text
from DBchunk import split_text
from DBembedding import get_embeddings
from chroma import ChromaDB

pdf_path = Path(__file__).parent / "虚幻引擎程序设计浅析.pdf"
print(pdf_path)
images = pdf_to_images_limit(pdf_path)

#OCR
texts= image_to_text(images)
#chunks
chunks = split_text(texts)
#embedding
embeddings = get_embeddings(chunks)
#存DB
db = ChromaDB()
db.add(
    chunks,
    embeddings
)
print("数据库建立完成")
