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
import random
import logging
import requests
import fitz

logging.basicConfig(format='%(asctime)s %(message)s', filename='ipcc_scraper.log', filemode='w', level=logging.INFO)

def setup_webdriver():
    """Setup and return a Selenium WebDriver with human-like behavior."""
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
    """Introduce a random delay to mimic human interaction."""
    time.sleep(random.uniform(min_delay, max_delay))

def sanitise_metadata(metadata):
    """Sanitise metadata by removing illegal characters."""
    custom_weights = "-!#$%&*.^_|~+\"\'(),/`~0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]abcdefghijklmnopqrstuvwxyz{} "
    
    def remove_illegal_chars(s):
        s = ''.join(c for c in s if c in custom_weights or c == ' ')
        s = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', s)
        return s[:255]

    sanitised_metadata = {remove_illegal_chars(key): remove_illegal_chars(str(value)) for key, value in metadata.items()}
    return sanitised_metadata

def get_ipcc_reports():
    """Get IPCC Assessment Reports and Special Reports (1995-2025)."""
    reports = []
    
    # AR6 Reports (2021-2023)
    ar6_reports = [
        {
            'title': 'AR6 Synthesis Report: Climate Change 2023',
            'url': 'https://www.ipcc.ch/report/ar6/syr/downloads/report/IPCC_AR6_SYR_LongerReport.pdf',
            'resource_type': 'Assessment Report',
            'year': '2023',
            'report_type': 'AR6 Synthesis'
        },
        {
            'title': 'AR6 Working Group I: The Physical Science Basis',
            'url': 'https://www.ipcc.ch/report/ar6/wg1/downloads/report/IPCC_AR6_WGI_Full_Report.pdf',
            'resource_type': 'Assessment Report',
            'year': '2021',
            'report_type': 'AR6 WG1'
        },
        {
            'title': 'AR6 Working Group II: Impacts, Adaptation and Vulnerability',
            'url': 'https://www.ipcc.ch/report/ar6/wg2/downloads/report/IPCC_AR6_WGII_Full_Report.pdf',
            'resource_type': 'Assessment Report',
            'year': '2022',
            'report_type': 'AR6 WG2'
        },
        {
            'title': 'AR6 Working Group III: Mitigation of Climate Change',
            'url': 'https://www.ipcc.ch/report/ar6/wg3/downloads/report/IPCC_AR6_WGIII_Full_Report.pdf',
            'resource_type': 'Assessment Report',
            'year': '2022',
            'report_type': 'AR6 WG3'
        }
    ]
    
    # Special Reports (2018-2019)
    special_reports = [
        {
            'title': 'Global Warming of 1.5°C (SR15)',
            'url': 'https://www.ipcc.ch/site/assets/uploads/sites/2/2022/06/SR15_Full_Report_LR.pdf',
            'resource_type': 'Special Report',
            'year': '2018',
            'report_type': 'SR15'
        },
        {
            'title': 'Climate Change and Land (SRCCL)',
            'url': 'https://www.ipcc.ch/site/assets/uploads/2019/11/SRCCL-Full-Report-Compiled-191128.pdf',
            'resource_type': 'Special Report',
            'year': '2019',
            'report_type': 'SRCCL'
        },
        {
            'title': 'Ocean and Cryosphere in a Changing Climate (SROCC)',
            'url': 'https://www.ipcc.ch/site/assets/uploads/sites/3/2022/03/SROCC_FullReport_FINAL.pdf',
            'resource_type': 'Special Report',
            'year': '2019',
            'report_type': 'SROCC'
        }
    ]
    
    # AR5 Reports (2013-2014)
    ar5_reports = [
        {
            'title': 'AR5 Synthesis Report: Climate Change 2014',
            'url': 'https://www.ipcc.ch/site/assets/uploads/2018/02/SYR_AR5_FINAL_full.pdf',
            'resource_type': 'Assessment Report',
            'year': '2014',
            'report_type': 'AR5 Synthesis'
        },
        {
            'title': 'AR5 Working Group I: Climate Change 2013 - The Physical Science Basis',
            'url': 'https://www.ipcc.ch/site/assets/uploads/2018/02/WG1AR5_all_final.pdf',
            'resource_type': 'Assessment Report',
            'year': '2013',
            'report_type': 'AR5 WG1'
        },
        {
            'title': 'AR5 Working Group II: Climate Change 2014 - Impacts, Adaptation and Vulnerability',
            'url': 'https://www.ipcc.ch/site/assets/uploads/2018/02/WGIIAR5-PartA_FINAL.pdf',
            'resource_type': 'Assessment Report',
            'year': '2014',
            'report_type': 'AR5 WG2'
        },
        {
            'title': 'AR5 Working Group III: Climate Change 2014 - Mitigation of Climate Change',
            'url': 'https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_full.pdf',
            'resource_type': 'Assessment Report',
            'year': '2014',
            'report_type': 'AR5 WG3'
        }
    ]
    
    # AR4 Reports (2007)
    ar4_reports = [
        {
            'title': 'AR4 Synthesis Report: Climate Change 2007',
            'url': 'https://www.ipcc.ch/site/assets/uploads/2018/02/ar4_syr_full_report.pdf',
            'resource_type': 'Assessment Report',
            'year': '2007',
            'report_type': 'AR4 Synthesis'
        }
    ]
    
    reports.extend(ar6_reports)
    reports.extend(special_reports)
    reports.extend(ar5_reports)
    reports.extend(ar4_reports)
    
    return reports

def sanitise_text(text):
    """Sanitise the text content to remove unwanted characters, keeping new lines."""
    sanitised = text.replace('\xad', '').replace('\x0c', '').replace('\x0b', '').replace('\x0e', '')
    sanitised = re.sub(r'[ \t]+', ' ', sanitised)
    sanitised = re.sub(r'(\s*\n\s*)+', '\n', sanitised)
    return sanitised.strip()

def main_ipcc_crawler(source, resource, negotiation_stream):
    """Main function to crawl, process, and upload IPCC data."""
    reports = get_ipcc_reports()
    logging.info(f"Processing {len(reports)} IPCC reports")
    
    category_name = source + '-' + resource
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    
    counter = 1
    for report in reports:
        try:
            pdf_url = report['url']
            pdf_filename = f"{counter}_{report['report_type']}_{report['year']}.pdf"
            counter += 1
            
            logging.info(f"Processing: {report['title']}")
            
            # Download PDF
            print(f"Downloading: {report['title']} ({pdf_url})")
            response = requests.get(pdf_url, headers=headers, stream=True)

            # Show download progress
            pdf_content = b''
            total_size = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    pdf_content += chunk
                    total_size += len(chunk)
                    if total_size % (1024*1024) == 0:  # Every MB
                        print(f"Downloaded {total_size // (1024*1024)}MB...")

            print(f"✓ Download complete: {total_size // (1024*1024)}MB")
            time.sleep(1)  # Reduced from 3 seconds
            
            if pdf_content:
                # Extract text using PyMuPDF
                pdf_document = fitz.open('pdf', pdf_content)
                text_content = ''
                for page in pdf_document:
                    text_content += page.get_text()
                pdf_document.close()
                
                sanitised_text_content = sanitise_text(text_content)
                summary = generate_summary_with_gpt3(sanitised_text_content)
                
                # Metadata
                slug = pdf_filename
                title = report['title']
                url = report['url']
                created = f"{report['year']}-01-01"
                document_type = 'Assessment Report'
                resource_type = report['resource_type']
                category = "IPCC" + ' - ' + resource_type
                
                logging.info(f"Category: {category}")
                
                output_filename = f"{pdf_filename}.txt"
                blob_save = f'{negotiation_stream}/{source}/staging_{category_name}'
                output_filepath = f'{blob_save}/{output_filename}'
                
                metadata = {
                    'Title': title,
                    'Name': report['report_type'],
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
                
                # Upload to blob
                blob_client.upload_blob(text_content, metadata=sanitised_metadata, overwrite=True)
                logging.info(f"Data for {pdf_filename} written to {output_filepath}")
                
                adjusted_delay(5, 8)
                
        except Exception as e:
            logging.error(f"Error processing {report['title']}: {e}")
            continue

def crawl_and_process_data(container_name, connection_string):
    """Crawl and process IPCC data."""
    source = 'ipcc'
    resource = 'assessment_reports'
    negotiation_streams = ['ipcc']
    
    for stream in negotiation_streams:
        main_ipcc_crawler(source=source, resource=resource, negotiation_stream=stream)
        # Skip database processing for now
        print(f"Completed scraping for {stream} stream")
        # conn = connect_database()
        # process_directory(conn, container_name, connection_string, f"{stream}/ipcc/staging_ipcc-assessment_reports", "public")
def main():
    load_dotenv(dotenv_path='../backend/.env')
    container_name = os.getenv('BLOB_CONTAINER_NAME')
    connection_string = os.getenv('BLOB_CONNECTION_STRING')
    
    # Crawl and process data
    crawl_and_process_data(container_name, connection_string)
    # Write to vector store  
    # write_to_vector(container_name, connection_string)

if __name__ == '__main__':
    main()