import requests
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

URLS = [
    "https://mwecau.ac.tz/",
    "https://mwecau.ac.tz/about",
    "https://mwecau.ac.tz/academics",
    "https://mwecau.ac.tz/programs/programs-list",
    "https://mwecau.ac.tz/programs/undergraduate",
    "https://mwecau.ac.tz/programs/post-graduate",
    "https://mwecau.ac.tz/programs/non-degree",
    "https://mwecau.ac.tz/campus-life",
    "https://mwecau.ac.tz/IT-services",
    "https://mwecau.ac.tz/library",
    "https://mwecau.ac.tz/mwecau-academic-staff",
    "https://mwecau.ac.tz/mwecau-administrative-staff",
    "https://mwecau.ac.tz/projects",
    "https://mwecau.ac.tz/outreach-programs",
    "https://mwecau.ac.tz/contact",
    "https://mwecau.ac.tz/admissions",
    "https://mwecau.ac.tz/fees",
    "https://mwecau.ac.tz/research",
]

CHROMA_PATH = "chroma_db"

def scrape(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        # remove nav, footer, scripts
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        print(f"Failed {url}: {e}")
        return ""

def build_vectorstore():
    print("Scraping MWECAU pages...")
    docs = []
    for url in URLS:
        text = scrape(url)
        if text:
            docs.append({"content": text, "source": url})
            print(f"  ✓ {url}")

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = []
    for doc in docs:
        splits = splitter.create_documents(
            [doc["content"]],
            metadatas=[{"source": doc["source"]}]
        )
        chunks.extend(splits)

    print(f"\nTotal chunks: {len(chunks)}")
    print("Building ChromaDB vector store...")

    # Use local embeddings — no API key, no internet, free
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"  # ~80MB, downloads once
    )

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    print("✓ Vector store built and saved to chroma_db/")

if __name__ == "__main__":
    build_vectorstore()