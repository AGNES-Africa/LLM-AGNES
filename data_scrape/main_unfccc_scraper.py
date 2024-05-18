import os
import time
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from azure.storage.blob import BlobServiceClient, BlobClient
from dotenv import load_dotenv
from utils.write_to_blob import *
from utils.open_ai_summary import *
from utils.credentials import *
from utils.write_to_postgres_db import *
from utils.existing_urls import *
from utils.reformat_date import *
import fitz
from utils.write_to_chroma_db import *

def setup_webdriver():
    """Initialise and return a configured instance of a Chrome WebDriver."""
    options = webdriver.ChromeOptions()
    prefs = {
        "plugins.always_authorize": True,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    options.add_experimental_option("prefs", prefs)
    driver_path = os.getenv('DRIVER_PATH')
    return webdriver.Chrome(options=options)

def connect_database():
    """Establish and return a database connection using the connection string from environment variables."""
    conn_str = get_uri()
    return psycopg2.connect(conn_str)

def get_blob_client(negotiation_stream, source, category_name, filename):
    """Return a BlobClient for a given file path in blob storage."""
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    blob_path = f'{negotiation_stream}/{source}/{category_name}/{filename}'
    return container_client.get_blob_client(blob_path)

def crawl_webpage(start, end, base_url, driver):
    """Crawl the specified webpage range and collect document links."""
    webpage_urls = []
    for page in range(start, end + 1):
        driver.get(f"{base_url}&page={page}")
        time.sleep(1)  # Allow time for the page to load
        elements_with_href = driver.find_elements(By.CSS_SELECTOR, "a[href*='/documents/']")
        title_elements = driver.find_elements(By.CLASS_NAME, "documentid")
        div_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'views-field-field-document-decision-symbol-1')]")

        for element, title_element, div_element in zip(elements_with_href, title_elements, div_elements):
            href = element.get_attribute('href')
            name = title_element.get_attribute("innerText")
            symbol = div_element.get_attribute("innerText").replace("Symbol: ", "")
            webpage_urls.append({'document_type': 'Decisions', 'url': href, 'document_name': name, 'document_symbol': symbol})
    print("Completed scraping webpage")
    driver.quit()
    return webpage_urls

def urls_set(all_urls):
    """Filter and return unique URLs."""
    seen_urls = set()
    filtered_hrefs = []

    for href in all_urls:
        if isinstance(href, dict) and 'url' in href and 'document_type' in href:
            url = href['url']
            if url not in seen_urls:
                filtered_hrefs.append(href)
                seen_urls.add(url)
    return filtered_hrefs

def process_urls(publications_url, driver):
    """Process each URL to extract necessary information and download PDFs."""
    print(f"Processing {len(publications_url)} URLs...")
    document_data = []

    for publication in publications_url:
        url = publication['url']
        driver.get(url)
        name = publication['document_symbol']
        title = publication['document_name']
        summary = driver.title
        publication_date = ''
        document_type = publication['document_type']
        pdf_href = ''

        try:
            publication_date_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.field--name-field-document-publication-date .field--item'))
            )
            publication_date = publication_date_element.text.strip()
        except NoSuchElementException:
            print(f"No publication date found for {url}")

        try:
            document_code_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.field--name-field-document-dsoc .field--item'))
            )
            document_code = document_code_element.text.strip()
        except NoSuchElementException:
            print(f"No document type found for {url}")

        try:
            open_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Open')]")
            pdf_href = open_link.get_attribute('href')
        except NoSuchElementException:
            try:
                pdf_link = driver.find_element(By.XPATH, "//a[contains(@href, 'E.pdf') or contains(innerText, 'English') or contains(@href, 'e.pdf') or contains(@href, 'eng') and substring(@href, string-length(@href) - string-length('.pdf') + 1) = '.pdf']")
                pdf_href = pdf_link.get_attribute('href')
            except NoSuchElementException:
                print(f"Element not found for {url}. Skipping...")
                continue

        if pdf_href:
            document_data.append({
                'url': pdf_href,
                'title': title,
                'summary': summary,
                'document_name': name,
                'created': publication_date,
                'document_code': document_code,
                'document_type': document_type
            })
            print(f"Completed processing {url}")
            time.sleep(4)
        else:
            print(f"No PDF link found for {url}")

        time.sleep(1)

    driver.quit()
    return document_data

def generate_url(negotiation_stream):
    """Generate and return the base URL for scraping."""
    base_url = 'https://unfccc.int/decisions'
    articles_per_page = 48
    return f'{base_url}?search2={negotiation_stream}&items_per_page={articles_per_page}'

def main_unfccc_crawler(driver, webpage, source, resource, negotiation_stream):
    """Main function to crawl, process, and upload data."""
    all_urls = crawl_webpage(0,1, webpage, driver)
    time.sleep(4)
    print("All URLs returned")
    time.sleep(4)
    driver = setup_webdriver()
    full_urls = process_urls(all_urls, driver)
    print("Full URLs returned")
    time.sleep(4)
    category_name = source + '-' + resource

    upload_file_to_blob(full_urls, negotiation_stream, source, category_name)
    time.sleep(2)
    driver.quit()
    print(f"Downloaded all files to {category_name}")
    
    counter = 1
    for item in full_urls:
        pdf_url = item['url']
        pdf_filename = f"{counter}_{pdf_url.split('/')[-1]}"
        counter +=1
        
        if pdf_filename.lower().endswith('.pdf'):
            # Download the PDF content directly without saving locally
            response = requests.get(pdf_url, headers=headers)
            time.sleep(3)
            pdf_content = response.content

            if pdf_content:
                try:
                    pdf_document = fitz.open('pdf', pdf_content)
                    text_content = ''
                    for page in pdf_document:
                        text_content+=page.get_text()
                    pdf_document.close()

                    #Get metadata and other relevant information
                    slug = item['document_code']
                    title = item['title']
                    url = item['url']
                    name = item['document_name']
                    created = reformat_date(item['created'])
                    document_type = item['document_type']
                    document_code = item['document_code']
                    category = source + ' - ' + resource
                    print("Category:", category)
                    summary = item['summary']
                    
                    output_filename = f"{pdf_filename}.txt"
                    blob_save = f'{negotiation_stream}/{source}/raw_{category_name}'
                    output_filepath = f'{blob_save}/{output_filename}'

                    metadata = {
                        'Title': title,
                        'Name': name,
                        'Slug': slug,
                        'URL': url,
                        'Created': created,
                        'Type': document_type,
                        'Code': document_code,
                        'Source': source,
                        'Resource': resource,
                        'Category': category,
                        'Summary': summary
                    }
                    blob_client = BlobClient.from_connection_string(
                        conn_str=connection_string,
                        container_name=container_name,
                        blob_name=output_filepath
                    )
                    # Upload the PDF content directly to the blob
                    blob_client.upload_blob(text_content, metadata=metadata, overwrite=True)
                    print(f"Data for {pdf_filename} written to {output_filepath}")
                except Exception as e:
                    print(f"URL file for {pdf_filename} could not be converted. Skipping...:{e}")
            else:
                print(f"Failed to extract text from {pdf_filename}")

def crawl_and_process_data(driver, container_name, connection_string):
    """Crawl and process data using the provided driver and directories."""
    source = 'unfccc'
    resource = 'decisions'
    negotiation_streams = ['agriculture','finance', 'gender'] #
    for stream in negotiation_streams:
        webpage = generate_url(stream)
        driver = setup_webdriver()
        main_unfccc_crawler(driver, webpage, source=source, resource=resource, negotiation_stream=stream)
        driver = setup_webdriver() 
        conn = connect_database()
        process_directory(conn, container_name, connection_string, f"{stream}/unfccc/raw_unfccc-decisions")

def main():
    load_dotenv()
    container_name = os.getenv('BLOB_CONTAINER_NAME')
    connection_string = os.getenv('BLOB_CONNECTION_STRING')
    driver = setup_webdriver()
    #crawl and process data from the web
    crawl_and_process_data(driver, container_name, connection_string)  
    #write to vector store  
    streams = ['agriculture', 'finance', 'gender']
    for stream_name in streams:
        write_to_vector(container_name,connection_string,stream_name)

if __name__ == '__main__':
    main()
