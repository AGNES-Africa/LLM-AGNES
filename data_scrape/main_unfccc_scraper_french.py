import os
import time
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
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
from webdriver_manager.chrome import ChromeType
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
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install()), options=options)
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

def extract_decision(text, symbol):
    """
    Extract decisions that match the given symbol.
    """
    # Regular expression to match "Decision" followed by the specific symbol
    decision_pattern = re.compile(rf'(Décision\s+{re.escape(symbol)}.*?)((?=Décision\s+\d+/\w+\.\d+\s+)|$)', re.DOTALL)

    # Find all matches for the decision pattern
    decisions = decision_pattern.findall(text)
    
    # Extract the decisions using the positions of the matches
    decision_texts = [match[0].strip() for match in decisions]
    decision = ''.join(decision_texts)
    if decision:
        return decision
    else:
        logging.info(f"Error: Decision not found for {symbol}")

def crawl_webpage(base_url, driver, stream):
    """Crawl the webpage, collect document links, and handle 'Load More' button dynamically."""
    driver.get(base_url)
    adjusted_delay(4, 6)
    webpage_urls = []

    def scrape_data():
        """Function to scrape data from the current state of the webpage."""
        elements_with_href = driver.find_elements(By.CSS_SELECTOR, "a[href*='/documents/']")
        title_elements = driver.find_elements(By.CLASS_NAME, "documentid")
        div_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'views-field-field-document-decision-symbol-1')]")

        for element, title_element, div_element in zip(elements_with_href, title_elements, div_elements):
            href = element.get_attribute('href')
            name = title_element.get_attribute("innerText").strip()
            raw_symbol = div_element.get_attribute("innerText").replace("Symbol: ", "")
            symbol = raw_symbol.replace(" ", "").upper().strip()
            webpage_urls.append({'document_type': 'Decisions', 'url': href, 'document_name': name, 'document_symbol': symbol})

    if stream == "finance":
        for page in range(0, 5):
            driver.get(f"{base_url}&page={page}")
            scrape_data()
            adjusted_delay(3, 5)
    else:
        # Initial scrape
        scrape_data()
   
    logging.info("Completed scraping webpage")
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
    # publications_url = urls_set(publications_url)
    logging.info(f"Processing {len(publications_url)} URLs...")
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
            logging.info(f"No publication date found for {url}")

        try:
            document_code_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.field--name-field-document-dsoc .field--item'))
            )
            document_code = document_code_element.text.strip()
        except NoSuchElementException:
            logging.info(f"No document type found for {url}")

        try:
            open_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Open')]")
            pdf_href = open_link.get_attribute('href')
        except NoSuchElementException:
            try:
                pdf_link = driver.find_element(By.XPATH, "//a[contains(@href, 'F.pdf') or contains(innerText, 'French') or contains(@href, 'f.pdf') or contains(@href, 'fr') and substring(@href, string-length(@href) - string-length('.pdf') + 1) = '.pdf']")
                pdf_href = pdf_link.get_attribute('href')
            except NoSuchElementException:
                logging.info(f"Element not found for {url}. Skipping...")
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
            logging.info(f"Completed processing {url}")
            adjusted_delay(4, 6)
        else:
            logging.info(f"No PDF link found for {url}")

        adjusted_delay(2, 4)

    driver.quit()
    return document_data

def sanitise_text(text):
    """Sanitise the text content to remove unwanted characters, keeping new lines."""
    # Remove unwanted characters
    sanitised = text.replace('\xad', '').replace('\x0c', '').replace('\x0b', '').replace('\x0e', '')
    
    # Replace multiple spaces with a single space, but keep new lines
    sanitised = re.sub(r'[ \t]+', ' ', sanitised)
    sanitised = re.sub(r'(\s*\n\s*)+', '\n', sanitised)
    
    return sanitised.strip()

def generate_url(negotiation_stream):
    """Generate and return the base URL for scraping."""
    base_url = 'https://unfccc.int/decisions'
    articles_per_page = 48
    return f'{base_url}?search2={negotiation_stream}&items_per_page={articles_per_page}'

def main_unfccc_crawler(driver, webpage, source, resource, negotiation_stream, language):
    """Main function to crawl, process, and upload data."""
    all_urls = crawl_webpage(webpage, driver, negotiation_stream)
    adjusted_delay(4, 6)
    logging.info("All URLs returned")
    adjusted_delay(4, 6)
    driver = setup_webdriver()
    adjusted_delay(4, 6)
    full_urls = process_urls(all_urls, driver)
    logging.info("Full URLs returned")
    adjusted_delay(4, 6)
    category_name = source + '-' + resource
    staging_dir = f"staging_{category_name}"
    os.makedirs(staging_dir, exist_ok=True)

    for item in full_urls:
        result = upload_file_to_blob(item, negotiation_stream, language, source, category_name)
        if result:
            entry, text_content = result
            symbol_corrected = entry.get('document_name').replace(" ", "").upper().strip()
            symbol = symbol_corrected
            logging.info(f"Symbol:{symbol}")
            title = ts.translate_text(entry.get('title'), translator='google', to_language='fr')
            if 'résolution' not in title.lower():
                logging.info(f"URL:{item.get('url')}")
                decision_text = extract_decision(text_content, symbol)

                # Store decisions in memory and upload directly
                if decision_text:
                    file_name = (symbol + '-' + title).replace(' ', '_').replace('/', '_')
                    decision_filename = f"{file_name}.txt"
                    logging.info(f"Decisions file name {decision_filename}")
                    # Upload each decision to the blob with metadata
                    decision_blob_path = f"{negotiation_stream}/french/{source}/staging_{category_name}/{decision_filename}"
                    decision_metadata = {
                        'Title': title,
                        'Name': symbol,
                        'Slug': decision_filename,
                        'URL': entry['url'],
                        'Created': reformat_date(entry['created']),
                        'Type': ts.translate_text(entry.get('document_type', 'Publication'), translator='google', to_language='fr'),
                        'Code': ts.translate_text(entry.get('document_code', ''), translator='google', to_language='fr'),
                        'Source': source,
                        'Resource': resource,
                        'Category': 'unfccc - decisions',
                        'Summary': ts.translate_text(entry.get('summary', ''), translator='google', to_language='fr')
                    }
                    decision_sanitised_metadata = sanitise_metadata(decision_metadata)
                    decision_blob_client = BlobClient.from_connection_string(
                        conn_str=connection_string,
                        container_name=container_name,
                        blob_name=decision_blob_path
                    )
                    decision_blob_client.upload_blob(decision_text, metadata=decision_sanitised_metadata, overwrite=True)
                    logging.info(f"Decision {decision_filename} written to {decision_blob_path}")

    # driver.quit()


def crawl_and_process_data(driver, container_name, connection_string):
    """Crawl and process data using the provided driver and directories."""
    source = 'unfccc'
    resource = 'decisions'
    language = 'french'
    negotiation_streams = ['agriculture', 'gender', 'finance']
    # negotiation_streams = ['finance'] # for testing
    for stream in negotiation_streams:
        webpage = generate_url(stream)
        driver = setup_webdriver()
        main_unfccc_crawler(driver, webpage, source=source, resource=resource, negotiation_stream=stream, language=language)
        conn = connect_database()
        process_directory(conn, container_name, connection_string, f"{stream}/{language}/unfccc/staging_unfccc-decisions", language)

def main():
    load_dotenv()
    container_name = os.getenv('BLOB_CONTAINER_NAME')
    connection_string = os.getenv('BLOB_CONNECTION_STRING')
    driver = setup_webdriver()
    adjusted_delay(4, 6)
    #crawl and process data from the web
    crawl_and_process_data(driver, container_name, connection_string)  
    # write to vector store  
    # write_to_vector(container_name,connection_string)

if __name__ == '__main__':
    main()
