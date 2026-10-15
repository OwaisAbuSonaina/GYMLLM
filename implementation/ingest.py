import os
import glob
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from dotenv import load_dotenv

MODEL = "gpt-4.1-nano"

DB_NAME = str(Path(__file__).parent.parent / "vector_db")
KNOWLEDGE_BASE = str(Path(__file__).parent.parent / "knowledge-base")

load_dotenv(override=True)

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")


def fetch_documents():
    """Loads markdown files from directory subfolders and tags them with their folder name."""
    folders = glob.glob(str(Path(KNOWLEDGE_BASE) / "*"))
    documents = []
    for folder in folders:
        if not os.path.isdir(folder):
            continue
        doc_type = os.path.basename(folder)
        loader = DirectoryLoader(
            folder, glob="**/*.md", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"}
        )
        folder_docs = loader.load()
        for doc in folder_docs:
            doc.metadata["doc_type"] = doc_type
            # Extract basic temporal metadata based on file modification time to aid temporal queries
            doc.metadata["last_modified"] = os.path.getmtime(doc.metadata["source"])
            documents.append(doc)
    return documents


def create_chunks(documents):
    """
    Splits documents using Markdown headers to preserve logical grouping of HR policies,
    then applies a token-based character splitter for any oversized sections.
    """
    # 1. Structure-aware splitting based on Markdown headers
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    
    # 2. Token-based fallback for sections that exceed the embedding window limits
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="o200k_base", 
        chunk_size=430, 
        chunk_overlap=60
    )
    
    final_chunks = []
    for doc in documents:
        # Split document logically by headers
        md_chunks = markdown_splitter.split_text(doc.page_content)
        
        # Transfer the original file metadata (doc_type, source, last_modified) to the new chunks
        for chunk in md_chunks:
            chunk.metadata.update(doc.metadata)
        
        # Apply token-based splitting for chunks that remain too large
        split_chunks = text_splitter.split_documents(md_chunks)
        final_chunks.extend(split_chunks)
        
    return final_chunks


def create_embeddings(chunks):
    """Embeds chunks and stores them in ChromaDB."""
    if os.path.exists(DB_NAME):
        Chroma(persist_directory=DB_NAME, embedding_function=embeddings).delete_collection()

    vectorstore = Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory=DB_NAME
    )

    collection = vectorstore._collection
    count = collection.count()

    sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]
    dimensions = len(sample_embedding)
    print(f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store")
    return vectorstore


if __name__ == "__main__":
    documents = fetch_documents()
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("Ingestion complete")