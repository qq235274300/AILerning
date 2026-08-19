from pdf2image import convert_from_path


# DirectX 12 3D 游戏开发实战_.pdf  虚幻引擎程序设计浅析.pdf
def pdf_to_images(pdf_path):
    images = convert_from_path(
        pdf_path,
        dpi=300,
        poppler_path=r"D:\Me\Release-26.02.0-0\poppler-26.02.0\Library\bin"
    )
    print(f"PDF页数:{len(images)}")
    return images

def pdf_to_images_limit(pdf_path,last_page = 20):
    images = convert_from_path(
        pdf_path,
        dpi=300,
        first_page=1,
        last_page=last_page,
        poppler_path=r"D:\Me\Release-26.02.0-0\poppler-26.02.0\Library\bin"
    )
    print(f"PDF页数:{len(images)}")
    return images

