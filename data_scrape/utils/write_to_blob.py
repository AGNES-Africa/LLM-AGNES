import pdfplumber
import os
import io
import requests
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

# Initialise the Azure Blob Service Client
connection_string = os.getenv('BLOB_CONNECTION_STRING')
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_name = os.getenv('BLOB_CONTAINER_NAME')

def upload_file_to_blob(pdf_urls, negotiation_stream, source, category_name):
    """ 
    Get the blob client for the container
    Iterate through the PDF URLs and upload each one
    Download the PDF from the URL
    """
    for entry in pdf_urls:      
        url_file = entry['url']
        print("URL file:", url_file)
        response = requests.get(url_file, headers=headers)
        
        if 'pdf' not in response.headers.get('Content-Type', '').lower():
            print(f"URL does not point to a PDF: {url_file}. Content-Type: {response.headers.get('Content-Type')}")
            continue

        pdf_data = response.content
        blob_directory =f'{negotiation_stream}/{source}/raw_{category_name}' 
        blob_slug = f"{url_file.split('/')[-1]}"
        blob_name = blob_directory + '/' + blob_slug

        blob_client = blob_service_client.get_blob_client(container_name, blob_name)
        
        # Upload the PDF as a blob
        content_settings = ContentSettings(content_type='application/pdf')
        blob_client.upload_blob(pdf_data, overwrite=True, content_settings=content_settings)
        print(f"File uploaded to {blob_name} in container {container_name}")

        # Process the PDF in memory
        with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text()

        yield entry, text
