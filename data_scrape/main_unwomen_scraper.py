import os
import time
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys
from azure.storage.blob import BlobServiceClient, BlobClient
from dotenv import load_dotenv
from utils.write_to_blob import *
from utils.open_ai_summary import *
from utils.credentials import *
from utils.write_to_postgres_db import *
from utils.existing_urls import *
from utils.reformat_date import *
from utils.write_to_vector_db import *
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import random
import logging

logging.basicConfig(format='%(asctime)s %(message)s', filename='scraper_loader.log', filemode='w', level=logging.INFO)

def setup_webdriver():
    """
    Setup and return a Selenium WebDriver with human-like behavior.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    return driver


def connect_database():
    """Establish and return a database connection using the connection string from environment variables."""
    conn_str = get_uri()
    return psycopg2.connect(conn_str)

def adjusted_delay(min_delay=1, max_delay=3):
    """
    Introduce a random delay to mimic human interaction.
    """
    time.sleep(random.uniform(min_delay, max_delay))


def get_blob_client(negotiation_stream, source, category_name, filename):
    """Return a BlobClient for a given file path in blob storage."""
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    blob_path = f'{negotiation_stream}/{source}/{category_name}/{filename}'
    return container_client.get_blob_client(blob_path)

def sanitise_metadata(metadata):
    custom_weights = "-!#$%&*.^_|~+\"\'(),/`~0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]abcdefghijklmnopqrstuvwxyz{} "
    MAX_METADATA_LENGTH = 255

    def remove_illegal_chars(s):
        sanitised = []
        for c in s:
            if c in custom_weights:
                sanitised.append(c)
            else:
                print(f"Illegal character encountered and removed: {repr(c)}")
        s = ''.join(sanitised)
        # Remove control characters
        s = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', s)
        return s[:MAX_METADATA_LENGTH]  # Truncate to max length

    print("Original metadata:", metadata)
    sanitised_metadata = {remove_illegal_chars(key): remove_illegal_chars(str(value)) for key, value in metadata.items()}
    print("Sanitised metadata:", sanitised_metadata)
    return sanitised_metadata

def crawl_webpage(driver, start, end):
    all_data = []

    # Function to get publication data for a un women pages and resource type
    def get_publication_data(resource_type_name, resource_type_code):
        for page in range(start, end + 1):
            url = base_url_template.format(resource_type_code, subject_area_code, page)
            driver.get(url)
            time.sleep(2)
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "views-row")))
            publication_links = driver.find_elements(By.CLASS_NAME, "views-row")

            for publication in publication_links:
                date_elements = publication.find_elements(By.CSS_SELECTOR, ".search-item-date")
                if date_elements:
                    date_text = date_elements[1].text if len(date_elements) > 1 else date_elements[0].text
                    title_element = publication.find_element(By.CSS_SELECTOR, ".search-item-title a")
                    href = title_element.get_attribute('href')
                    title_text = title_element.text
                    all_data.append({
                        'resource_type': resource_type_name,
                        'date': date_text,
                        'title': title_text,
                        'url': href
                    })

    # URL template
    base_url_template = "https://www.unwomen.org/en/digital-library/publications?topic=d7f4313c7a9446babcccc55bf262308d&f%5B0%5D=resource_type_publications%3A{}&f%5B1%5D=subject_area_publications%3A{}&page={}"

    # Resource type code
    subject_area_code = "1738"

    # Resource type codes mapped to their names
    resource_type_map = {
        "Briefs": "2120",
        "Research papers": "2117",
        "Manuals/guides": "1410",
        "Data/statistics": "1411",
        "Assessments": "2105",
        "Best practices": "2106",
        "Discussion papers": "2111",
        "Case studies": "2108",
        "Policy papers": "2115",
        "Evaluation reports": "2122",
        "Institutional reports": "2123",
        "Infographics": "2134",
        "Brochures": "2131",
        "Newsletters/magazines": "1435",
        "Annual reports": "2119",
        "Issue papers": "2135",
        "Resource kits": "2118",
        "Proceedings": "2116",
        "Project/programme reports": "1425",
        "Intergovernmental reports": "2158",
        "Position reports": "1440",
        "Strategic plans": "2129",
        "Flagship reports": "2112",
        "Expert group meeting reports": "2154"
    }

    # Iterate over the resource type map and collect data for each resource type
    for resource_type_name, resource_type_code in resource_type_map.items():
        try:
            print(f"Processing resource type: {resource_type_name}")
            get_publication_data(resource_type_name, resource_type_code)
        except Exception as e:
            print(f"Failed to retrieve data for resource type: {resource_type_name} with error: {e}")

    # Close the driver
    driver.quit()

    # Print and return the collected data
    for entry in all_data:
        print(f"Resource type: {entry['resource_type']} | Date: {entry['date']} | URL: {entry['url']}")
    return all_data

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
        resource_type = publication['resource_type']
        title = publication['title']
        publication_date = publication['date']
        pdf_href = ''
        summary = ''

        try:
             # Wait for all the links on the page to load
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href]")))
            
            # Find all links that end with .pdf
            pdf_links = driver.find_elements(By.CSS_SELECTOR, "a[href$='.pdf']")
    
            for pdf_link in pdf_links:
                pdf_href = pdf_link.get_attribute('href')
                if pdf_href:
                    # Add the .pdf href to the list
                    publication['url'] = pdf_href
                    time.sleep(2)

                    break  
        except NoSuchElementException:
            print(f"No PDF date found for {url}. Skipping...") 
            continue

        if pdf_href:
            document_data.append({
                'url': pdf_href,
                'title': title,
                'resource_type': resource_type,
                'created': publication_date,
                'document_type': 'Publication',
                'Summary': summary
            })
            print(f"Completed processing {url}")
            time.sleep(4)
        else:
            print(f"No PDF link found for {url}")

        time.sleep(1)

    driver.quit()
    return document_data

def sanitise_text(text):
    """Sanitise the text content to remove unwanted characters."""
    sanitised = text.replace('\xad', '').replace('\x0c', '').replace('\x0b', '').replace('\x0e', '')
    sanitised = re.sub(r'\s+', ' ', sanitised)
    return sanitised.strip()

def main_unwomen_crawler(driver, source, resource, negotiation_stream):
    """Main function to crawl, process, and upload data."""
    all_urls = crawl_webpage(driver, 0,1)
    adjusted_delay(4, 6)
    print("All URLs returned")
    adjusted_delay(4, 6)
    driver = setup_webdriver()
    full_urls = process_urls(all_urls, driver)
    print("Full URLs returned")
    adjusted_delay(4, 6)
    category_name = source + '-' + resource
    
    for item in full_urls:
        result = upload_file_to_blob(item, negotiation_stream, source, category_name)
        if result:
            entry, text_content = result
            sanitised_text_content = sanitise_text(text_content)
            summary = generate_summary_with_gpt3(sanitised_text_content)
            pdf_filename = entry['url'].split('/')[-1]
            #Get metadata and other relevant information
            slug = pdf_filename
            title = item['title']
            url = item['url']
            created = reformat_date(item['created'])
            document_type = item['document_type']
            resource_type = item['resource_type']
            category = "UN Women" + ' - ' + resource_type
            print("Category:", category)
            
            output_filename = f"{pdf_filename}.txt"
            blob_save = f'{negotiation_stream}/{source}/staging_{category_name}'
            output_filepath = f'{blob_save}/{output_filename}'

            metadata = {
                'Title': title,
                'Name': title,
                'Slug': slug,
                'URL': url,
                'Created': created,
                'Type': document_type,
                'ResourceType': resource_type,
                'Source': source,
                'Resource': resource,
                'Category': category,
                'Summary': summary
            }
            sanitised_metadata = sanitise_metadata(metadata)
            blob_client = BlobClient.from_connection_string(
                conn_str=connection_string,
                container_name=container_name,
                blob_name=output_filepath
            )
            # Upload the PDF content directly to the blob
            blob_client.upload_blob(text_content, metadata=sanitised_metadata, overwrite=True)
            print(f"Data for {pdf_filename} written to {output_filepath}")

def crawl_and_process_data(driver, container_name, connection_string):
    """Crawl and process data using the provided driver and directories."""
    source = 'un_women'
    resource = 'publications'
    # negotiation_streams = ['agriculture', 'gender', 'finance']
    negotiation_streams = ['gender'] # 
    for stream in negotiation_streams:
        # webpage = generate_url(stream)
        driver = setup_webdriver()
        main_unwomen_crawler(driver, source=source, resource=resource, negotiation_stream=stream)
        driver = setup_webdriver() 
        conn = connect_database()
        process_directory(conn, container_name, connection_string, f"{stream}/un_women/staging_un_women-publications")

def main():
    load_dotenv()
    container_name = os.getenv('BLOB_CONTAINER_NAME')
    connection_string = os.getenv('BLOB_CONNECTION_STRING')
    driver = setup_webdriver()
    #crawl and process data from the web
    crawl_and_process_data(driver, container_name, connection_string)  
    # # write to vector store  
    # write_to_vector(container_name,connection_string)

if __name__ == '__main__':
    main()
