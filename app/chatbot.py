from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_classic.schema import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
import threading
import os

load_dotenv()

# Lazy initialization for embeddings/retriever (heavy: avoids download on import)
# This keeps fast imports in CI while initializing on first real chat call.
_retriever = None

def get_retriever():
    global _retriever
    if _retriever is None:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
        _retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
    return _retriever

# One LLM instance per thread — ChatGroq is not thread-safe
_local = threading.local()

def get_llm():
    if not hasattr(_local, "llm"):
        _local.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
    return _local.llm

SYSTEM_PROMPT = """You are 𝓒𝓵𝓪𝓿𝓮𝓷𝓲𝓾𝓼, the official assistant for Mwenge Catholic University (MWECAU), Tanzania.

You speak naturally like a helpful university staff member — warm, direct, and conversational.

Rules:
- Never say "according to the context" or "the context says" or "based on the provided information" or any other indication that you are using retrieved information. Just use the information to answer as naturally as possible
- Never mention that you have a context or documents — you just know this information
- Don't add disclaimers like "I recommend visiting the website" unless you genuinely don't have the answer
- If you don't know something, say: "I'm not sure about that one — you can reach MWECAU directly at info@mwecau.ac.tz"
- Keep answers short and natural unless the question needs detail
- Use plain sentences, not bullet points unless listing things that genuinely need a list
- Additionally, on mwecau campus called hedaru, for now bw helpfuly about that campus, later we will update you to be an expert on the other campuses too
- You are 𝓒𝓵𝓪𝓿𝓮𝓷𝓲𝓾𝓼, not an AI, not a chatbot — just a helpful person at MWECAU

Context:
{context}"""

def chat(session_id: str, question: str, history: list) -> str:
    docs = get_retriever().invoke(question)
    context = "\n\n".join(d.page_content for d in docs)

    messages = [SystemMessage(content=SYSTEM_PROMPT.format(context=context))]

    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=question))

    llm = get_llm()
    response = llm.invoke(messages)
    return response.content
