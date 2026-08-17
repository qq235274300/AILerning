from paddleocr import PaddleOCR
import numpy as np
ocr = PaddleOCR(
    use_angle_cls = True,
    lang = "ch"
)

def image_to_text(images):
    texts=[]
    for index,image in enumerate(images):
        print(f"OSC 第{index}页")
        result = ocr.ocr(
            np.array(image),
            cls=True
            )
        page_text = ""
        if result[0]:
            for line in result[0]:
                text = line[1][0]
                page_text+= text
        texts.append(page_text)
    return texts