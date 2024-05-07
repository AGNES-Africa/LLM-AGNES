from scrapers.unfccc_scrape import *
from utils.open_ai_summary import *
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import time 
from dotenv import load_dotenv
from utils.credentials import *
from utils.existing_urls import *
from utils.write_to_postgres_db import *

load_dotenv()


# UNFCCC decisions Configuration Gender
def unfccc_main(driver_path, download_directory, save_directory, webpage, category):
    all_urls = crawl_webpage(0,1, webpage)
    time.sleep(4)
    unique_urls = urls_set(all_urls)
    time.sleep(4)
    full_urls = process_urls(unique_urls, driver)
    time.sleep(4)
    print(len(full_urls))
    # options.add_experimental_option("prefs", prefs)

    # driver = webdriver.Chrome(options=options)
    for publication in full_urls:
        download_pdf(publication['url'])

    driver.quit()

    print(f"Downloaded all files to {download_directory}")

    for item in full_urls:
        pdf_filename = item['url'].split('/')[-1]
        pdf_filepath = os.path.join(download_directory, pdf_filename)
        text = extract_from_pdf(pdf_filepath)
        
        if text:
            slug = item['document_code']  
            title = item['title']
            url = item['url']
            name = item['document_name']
            created = item['created']
            document_type = item['document_type']
            document_code = item['document_code']
            category = category
            summary = ''# Placeholder for the summary
            
            output_filename = f"{pdf_filename}.txt"
            output_filepath = os.path.join(save_directory, output_filename)

            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(f"Title: {title}\n")
                f.write(f"Name: {name}\n")
                f.write(f"Slug: {slug}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Created: {created}\n")
                f.write(f"Type:{document_type}\n")
                f.write(f"Code:{document_code}\n")
                f.write(f"Category:{category}\n")
                f.write(f"Summary:{summary}\n")
                f.write("Text:\n")
                f.write(text)
                print(f"Data for {url} written to {output_filepath}")
        else:
            print(f"Failed to extract text from {pdf_filepath}")

        process_files(save_directory)

driver_path = os.getenv('DRIVER_PATH')
download_directory = os.getenv('DOWNLOAD_DIRECTORY')
save_directory = os.getenv('SAVE_DIRECTORY')
webpage = os.getenv("WEB_PAGE")
conn_str = get_uri()
conn = psycopg2.connect(conn_str)
urls = get_urls_from_db(conn_str)
process_directory(save_directory, urls, conn)
conn.close()

# options.add_experimental_option("prefs", prefs)

# driver = webdriver.Chrome(options=options)
# unfccc_main(driver_path, download_directory, save_directory, webpage, category="Agriculture decisions")

