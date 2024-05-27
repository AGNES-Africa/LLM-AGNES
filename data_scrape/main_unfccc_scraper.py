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
import fitz
from utils.write_to_vector_db import *
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# def setup_webdriver():
#     """Initialise and return a configured instance of a Chrome WebDriver."""
#     options = webdriver.ChromeOptions()
#     prefs = {
#         "plugins.always_authorize": True,
#         "download.prompt_for_download": False,
#         "download.directory_upgrade": True,
#         "plugins.always_open_pdf_externally": True
#     }
#     options.add_experimental_option("prefs", prefs)
#     # driver_path = os.getenv("DRIVER_PATH")
#     return webdriver.Chrome(options=options)

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

def extract_decisions(text):
    """
    Extract decisions from the given text. Decisions start with "Decision" followed by a space and a number.
    """
    # Regular expression to match "Decision" followed by a space and a number
    decision_pattern = re.compile(r'Decision\s+\d+/CP\.\d+')
    
    # Find all matches for the decision pattern
    matches = list(re.finditer(decision_pattern, text))
    
    # Extract the decisions using the positions of the matches
    decisions = []
    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        decision_text = text[start:end].strip()
        decisions.append(decision_text)
    
    return decisions

def crawl_webpage(base_url, driver, stream):
    """Crawl the webpage, collect document links, and handle 'Load More' button dynamically."""
    driver.get(base_url)
    webpage_urls = []

    def scrape_data():
        """Function to scrape data from the current state of the webpage."""
        elements_with_href = driver.find_elements(By.CSS_SELECTOR, "a[href*='/documents/']")
        title_elements = driver.find_elements(By.CLASS_NAME, "documentid")
        div_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'views-field-field-document-decision-symbol-1')]")

        for element, title_element, div_element in zip(elements_with_href, title_elements, div_elements):
            href = element.get_attribute('href')
            name = title_element.get_attribute("innerText")
            symbol = div_element.get_attribute("innerText").replace("Symbol: ", "")
            webpage_urls.append({'document_type': 'Decisions', 'url': href, 'document_name': name, 'document_symbol': symbol})

    # Initial scrape
    scrape_data()
    if stream == "finance":
        count = 0
        while count < 9:
    # Process 'Load More' button if present
            try:
                load_more_button = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.LINK_TEXT, 'Load More')))
                if load_more_button and load_more_button.is_displayed():
                    load_more_button.send_keys(Keys.ENTER)
                    time.sleep(10)
                    scrape_data()  # Scrape hrefs loaded each time load more button is pressed
                    count += 1
            except TimeoutException:
                print("No more 'Load more' button to click.")
                break
            except Exception as e:
                print("An error occurred while trying to click the 'Load more' button:", e)
                break
    else:
        pass
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

def sanitise_text(text):
    """Sanitise the text content to remove unwanted characters."""
    sanitised = text.replace('\xad', '').replace('\x0c', '').replace('\x0b', '').replace('\x0e', '')
    sanitised = re.sub(r'\s+', ' ', sanitised)
    return sanitised.strip()

def generate_url(negotiation_stream):
    """Generate and return the base URL for scraping."""
    base_url = 'https://unfccc.int/decisions'
    articles_per_page = 48
    return f'{base_url}?search2={negotiation_stream}&items_per_page={articles_per_page}'
 

def main_unfccc_crawler(driver, webpage, source, resource, negotiation_stream):
    """Main function to crawl, process, and upload data."""
    all_urls = crawl_webpage(webpage, driver, negotiation_stream)
    time.sleep(4)
    print("All URLs returned")
    time.sleep(4)
    driver = setup_webdriver()
    full_urls = process_urls(all_urls, driver)
    print("Full URLs returned")
    time.sleep(4)
    category_name = source + '-' + resource
    staging_dir = f"staging_{category_name}"
    os.makedirs(staging_dir, exist_ok=True)

    upload_file_to_blob(full_urls, negotiation_stream, source, category_name)
    time.sleep(2)
    driver.quit()
    print(f"Downloaded all files to {category_name}")
    
    counter = 1
    for item in full_urls:
        pdf_url = item['url']
        pdf_filename = f"{counter}_{pdf_url.split('/')[-1]}"
        counter += 1
        
        if pdf_filename.lower().endswith('.pdf'):
            # Download the PDF content directly without saving locally
            response = requests.get(pdf_url)
            time.sleep(4)
            pdf_content = response.content

            if pdf_content:
                try:
                    # Check if the content is a valid PDF
                    if pdf_content[:4] != b'%PDF':
                        raise ValueError("Invalid PDF format")

                    pdf_document = fitz.open('pdf', pdf_content)
                    text_content = ''
                    for page in pdf_document:
                        text_content += page.get_text()
                    pdf_document.close()

                    if not text_content.strip():
                        raise ValueError("No text found in PDF")

                    sanitised_text_content = sanitise_text(text_content)
                    decisions = extract_decisions(sanitised_text_content)

                    # Store decisions in memory and upload directly
                    for i, decision in enumerate(decisions):
                        decision_filename = f"decision_{i+1}.txt"

                        # Upload each decision to the blob with metadata
                        decision_blob_path = f"{negotiation_stream}/{source}/staging_{category_name}/{decision_filename}"
                        decision_metadata = {
                            'Title': item['title'],
                            'Name': item.get('document_name', ''),
                            'Slug': decision_filename,
                            'URL': item['url'],
                            'Created': reformat_date(item['created']),
                            'Type': item.get('document_type', 'Publication'),
                            'Code': item.get('document_code', ''),
                            'Source': source,
                            'Resource': resource,
                            'Category': 'unfccc - decisions',
                            'Summary': item.get('summary', '')
                        }
                        decision_sanitised_metadata = sanitise_metadata(decision_metadata)
                        decision_blob_client = BlobClient.from_connection_string(
                            conn_str=connection_string,
                            container_name=container_name,
                            blob_name=decision_blob_path
                        )
                        decision_blob_client.upload_blob(decision, metadata=decision_sanitised_metadata, overwrite=True)
                        print(f"Decision {decision_filename} written to {decision_blob_path}")

                    # Get metadata and other relevant information
                    slug = item.get('document_code', '')
                    title = item['title']
                    url = item['url']
                    name = item.get('document_name', '')
                    created = reformat_date(item['created'])
                    document_type = item.get('document_type', 'Publication')
                    document_code = item.get('document_code', '')
                    category = source + ' - ' + resource
                    print("Category:", category)
                    summary = item.get('summary', '')
                    
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
                    sanitised_metadata = sanitise_metadata(metadata)
                    blob_client = BlobClient.from_connection_string(
                        conn_str=connection_string,
                        container_name=container_name,
                        blob_name=output_filepath
                    )
                    # Upload the combined PDF content directly to the blob
                    blob_client.upload_blob(sanitised_text_content, metadata=sanitised_metadata, overwrite=True)
                    print(f"Data for {pdf_filename} written to {output_filepath}")

                except (fitz.FileDataError, ValueError) as e:
                    print(f"URL file for {pdf_filename} could not be converted. Skipping...:{e}")
            else:
                print(f"Failed to extract text from {pdf_filename}")


def crawl_and_process_data(driver, container_name, connection_string):
    """Crawl and process data using the provided driver and directories."""
    source = 'unfccc'
    resource = 'decisions'
    #negotiation_streams = ['agriculture', 'gender', 'finance']
    negotiation_streams = ['agriculture'] # 
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
    # write to vector store  
    # write_to_vector(container_name,connection_string)

if __name__ == '__main__':
    main()
