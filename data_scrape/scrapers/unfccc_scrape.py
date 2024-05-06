import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from pdfminer.high_level import extract_text
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv

"""This scraper works for all unfccc documents and supporting files"""

load_dotenv()
download_directory = os.getenv('DOWNLOAD_DIRECTORY')

# Initialise the Chrome WebDriver
options = webdriver.ChromeOptions()
prefs = {
    "plugins.always-authorize": True,
    "download.default_directory": download_directory,
    "download.prompt_for_download": False,  
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True }

def crawl_webpage(start, end, base_url):
    driver = webdriver.Chrome(options=options)
    webpage_urls = [] 

    for page in range(start, end + 1):
        # Navigate to each page
        driver.get(f"{base_url}&page={page}")
        time.sleep(1)
        elements_with_href = driver.find_elements(By.CSS_SELECTOR, "a[href*='/documents/']")
        title_elements = driver.find_elements(By.CLASS_NAME, "documentid")
        div_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'views-field-field-document-decision-symbol-1')]")


        # Extract the href attribute from each element
        
        for element, title_element, div_element in zip(elements_with_href, title_elements, div_elements):
            href = element.get_attribute('href')
            name = title_element.get_attribute("innerText")
            symbol = div_element.get_attribute("innerText").replace("Symbol: ", "")
            webpage_urls.append({'document_type': 'Decisions',
                                 'url': href,
                                 'document_name': name,
                                 'document_symbol': symbol})
    print("Completed scraping webpage")
    # Once complete, close the driver
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


def download_pdf(url):
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)  
        print(f"Downloading file from {url}")
        time.sleep(2)
    except Exception as e:
        print(f"An error occurred: {e}")

def extract_slug(url):
    parsed_url = urlparse(url)
    slug = unquote(parsed_url.path).strip('/')
    return slug.split('/')[-1]  

def extract_from_html(url):
    driver.get(url)
    title = driver.title
    slug = extract_slug(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    text = ' '
    return slug, text

def extract_from_pdf(file_path):
    try:
        text = extract_text(file_path)
        return text
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        return None
