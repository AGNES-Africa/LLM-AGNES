import os 
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv


load_dotenv()
api_key = os.getenv('OPEN_API_KEY')
os.environ["OPENAI_API_KEY"]=api_key

def generate_summary_with_gpt3(text):
    """
    This function sends the provided text to OpenAI's GPT-3 model to generate a summary.
    """
    llm = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo')
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=20)
    chunks = text_splitter.create_documents([text])
    concatenated_text = " ".join([chunk.page_content for chunk in chunks])
    chain = load_summarize_chain(
        llm,
        chain_type='map_reduce',
        verbose=False
    )
    summary = chain.run(input_documents=chunks)
    return summary