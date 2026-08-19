from paddleocr import PaddleOCR
import numpy as np
ocr = PaddleOCR(
    use_angle_cls = True,
    lang = "ch"
)

def image_to_documents(images, source: str):
    documents=[]
    for index,image in enumerate(images):
        page = index + 1 
        print(f"OSC 第{page}页")
        result = ocr.ocr(
            np.array(image),
            cls=True
            )
        page_text = ""
        if result and result[0]:
            for line in result[0]:
                text = line[1][0]
                page_text += text + "\n"
        documents.append(
            {
            "page_content": page_text,
            "metadata":{
                "source": source,
                "page": page
            }
            }
        )    
    return documents
