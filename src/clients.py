from dotenv import load_dotenv
from perplexity import Perplexity
from openai import OpenAI
from google import genai
load_dotenv()

openai_client = OpenAI()
gemini_client = genai.Client()
perplexity_client = Perplexity()