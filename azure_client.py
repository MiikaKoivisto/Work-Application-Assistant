import os
import streamlit as st

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def get_setting(name):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass

    return os.getenv(name)


azure_openai_endpoint = get_setting("AZURE_OPENAI_ENDPOINT")
model_deployment = get_setting("MODEL_DEPLOYMENT")
embedding_deployment = get_setting("EMBEDDING_DEPLOYMENT")
azure_openai_api_key = get_setting("AZURE_OPENAI_API_KEY")


if not azure_openai_endpoint:
    raise ValueError("AZURE_OPENAI_ENDPOINT is missing.")

if not model_deployment:
    raise ValueError("MODEL_DEPLOYMENT is missing.")

if not embedding_deployment:
    raise ValueError("EMBEDDING_DEPLOYMENT is missing.")

if not azure_openai_api_key:
    raise ValueError("AZURE_OPENAI_API_KEY is missing.")


client = OpenAI(
    base_url=azure_openai_endpoint,
    api_key=azure_openai_api_key
)


def ask_ai(messages):
    response = client.responses.create(
        model=model_deployment,
        input=messages
    )

    return response.output_text


def create_embedding(text):
    response = client.embeddings.create(
        model=embedding_deployment,
        input=text
    )

    return response.data[0].embedding