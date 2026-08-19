from langchain_text_splitters import RecursiveCharacterTextSplitter
def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000,
        chunk_overlap = 200
    )
    chunks = []
    for document in documents:
        texts = splitter.split_text(
            document["page_content"]
        )
        for index,text in enumerate(texts):
            metadata = document["metadata"].copy()
            metadata["chunk_index"] = index
            chunks.append(
                {
                    "page_content": text,
                    "metadata": metadata
                }
            )
    print(
        "chunk数量:",
        len(chunks) 
    )
    return chunks
