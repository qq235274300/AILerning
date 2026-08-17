from langchain_text_splitters import RecursiveCharacterTextSplitter
def split_text(texts):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000,
        chunk_overlap = 200
    )
    chunks = splitter.split_text(
        "\n".join(texts)
    )
    print(
        "chunk数量:",
        len(chunks) 
    )
    return chunks