import psycopg2
import string
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import AzureBlobStorageFileLoader
from azure.storage.blob import BlobServiceClient
import re
from utils.credentials import *
from langchain_text_splitters import RecursiveCharacterTextSplitter


text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", "  ", " ", ""],
    chunk_size=512,
    chunk_overlap=100,
    length_function=len,
    is_separator_regex=False,
)


def normalise_blob_name(blob_name):
    # Extract the filename and remove any leading digits and an underscore
    normalised_name = blob_name.split('/')[-1]  # Get the last part after '/'
    # normalised_name = re.sub(r'^\d+_', '', filename)  # Remove leading digits and an underscore
    return normalised_name


def chunk_text(text):
    return text_splitter.split_text(text)


def get_blob_raw_text(blob_connection_string, blob_container_name, blob, skip_to_first_decision=False):
    loader = AzureBlobStorageFileLoader(conn_str=blob_connection_string, container=blob_container_name, blob_name=blob.name)
    documents = loader.load()

    raw_text_result = ""

    for document in documents:
        raw_text = document.page_content

        # filter text to remove non-printable characters (not relevant for french documents)
        # raw_text = "".join(filter(lambda char: char in string.printable + "–", raw_text))

        # deal with multiple spaces
        raw_text = re.sub("\s+"," ",raw_text)
        
        if skip_to_first_decision:
            # skip over table of contents and jump to first decision
            raw_text = raw_text[next(re.finditer("Décision \d", raw_text)).span()[0]:]

        raw_text_result += raw_text

    return raw_text_result


def write_to_vector(blob_container_name, blob_connection_string):
    conn = psycopg2.connect(get_uri())
    cursor = conn.cursor()

    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_client = blob_service_client.get_container_client(blob_container_name)

    embedding = OpenAIEmbeddings(model="text-embedding-3-small")
    processed_blobs = {}

    for blob in container_client.list_blobs():
        if (blob.name.endswith('.txt')):
            normalised_name = normalise_blob_name(blob.name)

            if normalised_name not in processed_blobs:
                processed_blobs[normalised_name] = True

                blob_client = container_client.get_blob_client(blob)
                metadata = blob_client.get_blob_properties().metadata

                # Write proceedings documents to vector DB
                if ("raw_unfccc-decisions" in blob.name) and ("french" in blob.name):

                    raw_text = get_blob_raw_text(blob_connection_string, blob_container_name, blob, skip_to_first_decision=True)

                    if(len(raw_text) > 0):
                        cursor.execute("SELECT COALESCE(MAX(id)+1,1) AS id FROM embed.french_proceedings_documents")
                        document_id = cursor.fetchone()[0]

                        cursor.execute(
                            "INSERT INTO embed.french_proceedings_documents (id, title, url) VALUES (%s, %s, %s)",
                            (
                                document_id, 
                                (metadata.get('Summary'))[0:200], 
                                metadata.get('URL', 'Default URL')
                            )
                        )

                        chunks = chunk_text(raw_text)
                        for chunk in chunks:
                            embedding_vector = embedding.embed_query(chunk)
                            cursor.execute(
                                "INSERT INTO embed.french_proceedings_embeddings (vector, content, document_id) VALUES (%s, %s, %s)",
                                (embedding_vector, chunk, document_id)
                            )

                        conn.commit()
                    
                        print(f"Document: {normalised_name} successfully added to vector db with unique handling.")


                # Write individual decisions to a separate vector DB
                if ("staging_unfccc-decisions" in blob.name):

                    raw_text = get_blob_raw_text(blob_connection_string, blob_container_name, blob)

                    if(len(raw_text) > 0):
                        summary = metadata.get('Name') + " - " + metadata.get('Title')

                        cursor.execute("SELECT COALESCE(MAX(id)+1,1) AS id FROM embed.french_decisions_documents")
                        document_id = cursor.fetchone()[0]

                        cursor.execute(
                            "INSERT INTO embed.french_decisions_documents (id, title, title_vector, url, created_date) VALUES (%s, %s, %s, %s, %s)",
                            (
                                document_id, 
                                summary[0:200],
                                embedding.embed_query(summary),
                                metadata.get('URL', 'Default URL'),
                                metadata.get('Created')
                            )
                        )

                        chunks = chunk_text(raw_text)
                        for chunk in chunks:
                            embedding_vector = embedding.embed_query(chunk)
                            cursor.execute(
                                "INSERT INTO embed.french_decisions_embeddings (vector, content, document_id) VALUES (%s, %s, %s)",
                                (embedding_vector, chunk, document_id)
                            )

                        conn.commit()
                    
                        print(f"Document: {normalised_name} successfully added to vector db with unique handling.")

    cursor.close()
    conn.close()                
              

