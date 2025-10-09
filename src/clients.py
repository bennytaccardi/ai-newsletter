import chromadb
from dotenv import load_dotenv
from perplexity import Perplexity
from openai import OpenAI
from google import genai
load_dotenv()

chroma_client = chromadb.HttpClient(host='localhost', port=8000)
chroma_client.heartbeat()
openai_client = OpenAI()
gemini_client = genai.Client()
perplexity_client = Perplexity()