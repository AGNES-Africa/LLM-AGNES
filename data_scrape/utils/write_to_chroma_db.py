import psycopg2
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import AzureBlobStorageFileLoader
from azure.storage.blob import BlobServiceClient
import re
from utils.credentials import *
import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=200,
    length_function=len,
    is_separator_regex=False,
)

def normalise_blob_name(blob_name):
    # Extract the filename and remove any leading digits and an underscore
    filename = blob_name.split('/')[-1]  # Get the last part after '/'
    normalised_name = re.sub(r'^\d+_', '', filename)  # Remove leading digits and an underscore
    return normalised_name

def chunk_text(text):
    return text_splitter.split_text(text)

def write_to_vector(blob_container_name, blob_connection_string):
    conn = psycopg2.connect(get_uri())
    cursor = conn.cursor()

    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_client = blob_service_client.get_container_client(blob_container_name)

    embedding = OpenAIEmbeddings(model="text-embedding-3-small")
    processed_blobs = {}

    for blob in container_client.list_blobs():
        if blob.name.endswith('.txt'):
            normalised_name = normalise_blob_name(blob.name)
            if normalised_name not in processed_blobs:
                processed_blobs[normalised_name] = True
                blob_client = container_client.get_blob_client(blob)
                metadata = blob_client.get_blob_properties().metadata

                loader = AzureBlobStorageFileLoader(conn_str=blob_connection_string, container=blob_container_name, blob_name=blob.name)
                documents = loader.load()

                for document in documents:
                    chunks = chunk_text(document.page_content)
                    for chunk in chunks:
                        embedding_vector = embedding.embed_query(chunk)
                        cursor.execute(
                            "INSERT INTO embed.document_embeddings (title, url, slug, vector) VALUES (%s, %s, %s, %s)",
                            (metadata.get('Summary', 'Default Title'), metadata.get('URL', 'Default URL'), normalised_name, embedding_vector)
                        )
                        conn.commit()

                print(f"Document: {normalised_name} successfully added to vector db with unique handling.")

    cursor.close()
    conn.close()                
              

