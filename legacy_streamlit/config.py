from dotenv import load_dotenv, find_dotenv
import os

_ = load_dotenv(find_dotenv())

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DATA_FOLDER = "extratos"
OUTPUT_CSV = "finances.csv"
