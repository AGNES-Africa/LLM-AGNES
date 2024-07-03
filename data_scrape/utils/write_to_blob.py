import pdfplumber
import os
import io
import re
import requests
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

from translate import Translator
translator= Translator(to_lang="fr")


# Load environment variables
load_dotenv()

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

# Initialise the Azure Blob Service Client
connection_string = os.getenv('BLOB_CONNECTION_STRING')
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_name = os.getenv('BLOB_CONTAINER_NAME')

def sanitise_metadata(metadata):
    """
    Sanitise metadata by removing illegal characters.
    """
    custom_weights = "-!#$%&*.^_|~+\"\'(),/`~0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]abcdefghijklmnopqrstuvwxyz{} "
    
    def remove_illegal_chars(s):
        # Remove characters not in custom_weights
        s = ''.join(c for c in s if c in custom_weights or c == ' ')
        # Remove control characters
        s = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', s)
        return s[:255]  # Truncate to max length

    sanitised_metadata = {remove_illegal_chars(key): remove_illegal_chars(str(value)) for key, value in metadata.items()}
    return sanitised_metadata


def upload_file_to_blob(entry, negotiation_stream, language, source, category_name):
    """ 
    Get the blob client for the container
    Iterate through the PDF URLs and upload each one
    Download the PDF from the URL
    """
    
    url_file = entry['url']
    print("URL file:", url_file)
    response = requests.get(url_file, headers=headers)
    
    if 'pdf' not in response.headers.get('Content-Type', '').lower():
        print(f"URL does not point to a PDF: {url_file}. Content-Type: {response.headers.get('Content-Type')}")
        return None

    pdf_data = response.content
    blob_directory =f'{negotiation_stream}/{language}/{source}/raw_{category_name}' 
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

        blob_client_txt = blob_service_client.get_blob_client(container_name, f"{blob_name}.txt")
        text_metadata = {
            'URL': entry['url'],
            'Summary': translator.translate(entry.get('summary', ''))
        }
        text_sanitised_metadata = sanitise_metadata(text_metadata)
        blob_client_txt.upload_blob(text, metadata=text_sanitised_metadata, overwrite=True)

    return entry, text
