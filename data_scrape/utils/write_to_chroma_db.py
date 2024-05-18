import psycopg2
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import AzureBlobStorageFileLoader
from azure.storage.blob import BlobServiceClient
import re
from utils.credentials import *

def normalise_blob_name(blob_name):
    # Extract the filename and remove any leading digits and an underscore
    filename = blob_name.split('/')[-1]  # Get the last part after '/'
    normalised_name = re.sub(r'^\d+_', '', filename)  # Remove leading digits and an underscore
    return normalised_name


def chunk_text(text, max_token_size=512):
    words = text.split()
    ideal_size = int(max_token_size * 4 / 3)
    chunks = [' '.join(words[i:i+ideal_size]) for i in range(0, len(words), ideal_size)]
    return chunks

def process_embeddings(vector):
    # Ensure the vector length matches the database expected size of 1536
    if len(vector) < 1536:
        # Extend vector with zeros if it's too short
        return np.pad(vector, (0, 1536 - len(vector)), 'constant')
    elif len(vector) > 1536:
        # Truncate vector if it's too long
        return vector[:1536]
    return vector

def write_to_vector(blob_container_name, blob_connection_string, stream_name):
    conn = psycopg2.connect(get_uri())
    cursor = conn.cursor()

    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_client = blob_service_client.get_container_client(blob_container_name)

    embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
    processed_blobs = {}

    for blob in container_client.list_blobs():
        if blob.name.endswith('.txt') and blob.name.startswith(f'{stream_name}/'):
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
                        processed_vector = process_embeddings(embedding_vector)
                        cursor.execute(
                            "INSERT INTO embed.document_embeddings (title, url, slug, vector) VALUES (%s, %s, %s, %s)",
                            (metadata.get('Title', 'Default Title'), metadata.get('URL', 'Default URL'), normalised_name, processed_vector)
                        )
                        conn.commit()

                print(f"Document: {normalised_name} successfully added to vector db with unique handling.")

    cursor.close()
    conn.close()                
              

