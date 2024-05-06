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
    llm.get_num_tokens(text)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=20)
    chunks = text_splitter.create_documents([text])
    chain = load_summarize_chain(
    llm,
    chain_type='map_reduce',
    verbose=False
    )
    summary = chain.run(chunks)

    return summary

def process_files(directory_path):
    for file_path in Path(directory_path).glob('*.txt'):
        with open(file_path, 'r') as file:
            lines = file.readlines()
        for i, line in enumerate(lines):
            if line.startswith("Summary:"):
                if not line.strip().endswith("Summary:"):  
                    continue  
                text = "".join(lines)
                summary = generate_summary_with_gpt3(text)
                
                lines[i] = f"Summary: {summary}\n"
                break
        
        with open(file_path, 'w') as file:
            file.writelines(lines)
