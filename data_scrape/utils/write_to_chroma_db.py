import os
import psycopg
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import AzureBlobStorageFileLoader, TextLoader
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
import re
from utils.credentials import *

def normalise_blob_name(blob_name):
    # Extract the filename and remove any leading digits and an underscore
    filename = blob_name.split('/')[-1]  # Get the last part after '/'
    normalised_name = re.sub(r'^\d+_', '', filename)  # Remove leading digits and an underscore
    return normalised_name


def write_to_vector(blob_container_name,blob_connection_string, stream_name):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    blob_container_name = os.getenv("BLOB_CONTAINER_NAME")
    blob_connection_string = os.getenv("BLOB_CONNECTION_STRING")

    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_client = blob_service_client.get_container_client(blob_container_name)

    blobs = container_client.list_blobs()
    processed_blobs = {}

    for blob in blobs:
        if blob.name.lower().endswith('.txt') and blob.name.startswith(f'{stream_name}'):
            normalised_name = normalise_blob_name(blob.name)
            print("Normalised blob:", normalised_name)
            if normalised_name not in processed_blobs:
                blob_client = container_client.get_blob_client(blob)
                metadata = blob_client.get_blob_properties().metadata  # Fetch metadata

                title = metadata.get('Title', 'Default Title')
                url = metadata.get('URL', 'Default URL')
                loader = AzureBlobStorageFileLoader(
                    conn_str=blob_connection_string,
                    container=blob_container_name,
                    blob_name=blob.name
                )
                documents = loader.load()
                print("Documents loaded to Azure Blob storage file loader")


                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                texts = text_splitter.split_documents(documents)
                print("Text split completed")

                embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
                print("Embeddings created")
                conn_string = get_uri(use_sqlalchemy=True)

                db = PGVector.from_documents(
                    embedding=embedding,
                    documents=texts,
                    collection_name="llm_corpus_collection",
                    connection=conn_string
                )
                ids = [title for doc in documents if title in metadata]
                db.add_documents(texts, id=ids)
                print(f"Document: {normalised_name} successfully added to vector db")

                processed_blobs[normalised_name] = True  # Mark this normalised name as processed

# Query
# retriever = db.as_retriever()

# query = "What is the decision on agriculture?"

# # LLM will default to text-davinci-003 because we are using a completion endpoint
# # versus a chat endpoint
# qa = RetrievalQA.from_chain_type(llm=OpenAI(), chain_type="stuff", retriever=retriever)

# answer = qa.run(query)

# print(answer)

