import os
import time
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from azure.storage.blob import BlobServiceClient, BlobClient
from utils.write_to_blob import *
from utils.open_ai_summary import *
from utils.credentials import *
from utils.write_to_postgres_db import *
from utils.existing_urls import *

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from dotenv import load_dotenv



# Function to get the directory path (now used for blob path construction)

def get_directory(negotiation_stream, source, category_name):
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    directory = f'{negotiation_stream}/{source}/{category_name}'
    return container_client.get_blob_client(directory)



def serialize_blob_client(blob_client):
    return {
        'url': blob_client.url,
        'container_name': blob_client.container_name,
        'blob_name': blob_client.blob_name
    }

# Define the directories to download and save files
# download_directory = serialize_blob_client(get_directory('agriculture', 'unfccc', 'raw_unfccc-decisions'))
# save_directory = serialize_blob_client(get_directory('agriculture', 'unfccc', 'unfccc-decisions'))


download_directory = get_directory('agriculture', 'unfccc', 'raw_unfccc-decisions').url
save_directory = get_directory('agriculture', 'unfccc', 'unfccc-decisions').url
print("Download Directory:", download_directory)
print("Save Directory:", save_directory)

# Initialise Chrome WebDriver
options = webdriver.ChromeOptions()
prefs = {
    "plugins.always-authorize": True,
    "download.prompt_for_download": False,
    "download.default_directory": download_directory,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True
}
options.add_experimental_option("prefs", prefs)

def crawl_webpage(start, end, base_url):
    driver = webdriver.Chrome(options=options)
    webpage_urls = []
    for page in range(start, end + 1):
        driver.get(f"{base_url}&page={page}")
        time.sleep(1)  # Allow time for the page to load
        # Collecting document links
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
    print(f"Processing {len(publications_url)} URLs...")
    document_data = []
    
    for publication in publications_url:
        url = publication['url']
        driver.get(url)
        name = publication['document_symbol'] + " - " + publication['document_name'] 
        title = driver.title
        publication_date = ''
        document_type = publication['document_type']
        pdf_href = ''

        try:
            publication_date_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '.field--name-field-document-publication-date .field--item'))
            )
            publication_date = publication_date_element.text.strip()
        except NoSuchElementException:
            print(f"No publication date found for {url}")

        try:
            document_code_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '.field--name-field-document-dsoc .field--item'))
            )
            document_code = document_code_element.text.strip()
        except NoSuchElementException:
            print(f"No document type found for {url}")

        try:
            # First, try to find the 'Open' link directly.
            open_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Open')]")
            pdf_href = open_link.get_attribute('href')
        except NoSuchElementException:
            # If no 'Open' link is found, then directly look for PDF links.
            pdf_link = driver.find_element(By.XPATH, "//a[contains(@href, 'E.pdf') or contains(@href, 'eng') and substring(@href, string-length(@href) - string-length('.pdf') + 1) = '.pdf']")
            if pdf_link:
                pdf_href = pdf_link.get_attribute('href')
            else:
                continue     # Assuming we take the first PDF link found

        if pdf_href:
            document_data.append({
                'url': pdf_href,
                'title': title,
                'document_name': name,
                'created': publication_date,
                'document_code': document_code,
                'document_type': document_type
            })
            print(f"Completed processing {url}")
            time.sleep(4)
        else:
            print(f"No PDF link found for {url}")

        # A brief pause to prevent overwhelming the server
        time.sleep(1)

    driver.quit()
    return document_data
   
def generate_url(negotiation_stream):
    base_url = 'https://unfccc.int/decisions'
    articles_per_page = 48
    return f'{base_url}?search2={negotiation_stream}&items_per_page={articles_per_page}'

# for download directory, raw files
negotiation_stream = 'agriculture'
source = 'unfccc'
category_name = 'unfccc-decisions'
load_dotenv()

driver_path = os.getenv('DRIVER_PATH')
conn_str = get_uri()
conn = psycopg2.connect(conn_str)
urls = get_urls_from_db(conn_str)

# Generate URLs
agriculture_url = generate_url('agriculture')
gender_url = generate_url('gender')
finance_url = generate_url('finance')

# UNFCCC corpus main scraper 
def main_unfccc_crawler(driver, download_directory, save_directory, webpage, source, resource):
    all_urls = crawl_webpage(0,1, webpage)
    time.sleep(4)
    unique_urls = urls_set(all_urls)
    print("Unique URLs:",unique_urls)
    time.sleep(4)
    # driver = webdriver.Chrome(options=options)
    full_urls = process_urls(unique_urls, driver)
    print("Full URLs:", full_urls)
    time.sleep(4)
    # print(full_urls) # Uncomment for debugging
    options.add_experimental_option("prefs", prefs)

    
    for entry in full_urls:
        # print(entry) # Uncomment for debugging
        upload_file_to_blob(entry, negotiation_stream, source, category_name)
    

    driver.quit()

    print(f"Downloaded all files to {category_name}")

    for item in full_urls:
        pdf_filename = item['url'].split('/')[-1]
        pdf_filepath = os.path.join(download_directory, pdf_filename)
        text = download_blob_to_string(blob_service_client, container_name, negotiation_stream, source, category_name, pdf_filename)
        
        if text:
            slug = item['document_code']  
            title = item['title']
            url = item['url']
            name = item['document_name']
            created = item['created']
            document_type = item['document_type']
            document_code = item['document_code']
            source = source
            resource = resource
            category = source + ' ' + '-' + ' ' + resource
            summary = ''# Placeholder for the summary
            
            output_filename = f"{pdf_filename}.txt"
            blob_save = f'{negotiation_stream}/{source}/raw_{category_name}'
            output_filepath = f'{blob_save}/{output_filename}'
            # print(output_filepath) # Uncomment for debugging

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
            blob_client.upload_blob(text, metadata=metadata, overwrite=True)
            print(f"Data for {url} written to {output_filepath}")
        else:
            print(f"Failed to extract text from {pdf_filepath}")

    process_files(save_directory)

options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=options)

agriculture_unfccc_crawler = main_unfccc_crawler(driver, download_directory, save_directory, agriculture_url, source="unfccc", resource="decisions")
agriculture_unfccc_write_to_postgres = process_directory(urls, conn, container_name, connection_string, "agriculture/unfccc/raw_unfccc-decisions")
conn.close()

