import pdfplumber
import os
import io
import requests
from pdfminer.high_level import extract_text
from azure.storage.blob import BlobServiceClient, BlobClient
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

# Initialise the Azure Blob Service Client
connection_string = os.getenv('BLOB_CONNECTION_STRING')
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_name = os.getenv('BLOB_CONTAINER_NAME')

def upload_file_to_blob(pdf_urls,negotiation_stream, source, category_name):
    """ 
        Get the blob client for the container
        Iterate through the PDF URLs and upload each one
        Download the PDF from the URL
    """
    url_file = pdf_urls['url']
    print("URL file:", url_file)
    pdf_data = requests.get(url_file, headers=headers).content
    print("PDF DATA:", len(pdf_data))
    blob_directory =f'{negotiation_stream}/{source}/raw_{category_name}' 
    blob_name = blob_directory + '/' + url_file.split("/")[-1]
    blob_client = blob_service_client.get_blob_client(container_name, blob_name)
    
    # Upload the PDF as a blob
    blob_client.upload_blob(pdf_data, overwrite=True)
    print(f"File uploaded to {blob_name} in container {container_name}")

def download_blob_to_string(blob_service_client, container_name, negotiation_stream, source, category_name, blob_name):
    blob_path = f'{negotiation_stream}/{source}/raw_{category_name}/{blob_name}'
    if not os.path.exists(blob_path):
        os.makedirs(blob_path)
    print(f"Blob path: {blob_path}")
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
    downloader = blob_client.download_blob(max_concurrency=1)

    # Extract the text from the PDF in memory using pdfplumber
    with pdfplumber.PDF(io.BytesIO(downloader.readall())) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()

    # Save the extracted text to a .txt file
    with open(f'{blob_path}{blob_name}.txt', 'wb') as file:
        file.write(text.encode())
        print(len(text))

    return text
