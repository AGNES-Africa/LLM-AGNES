#!/usr/bin/env python
# coding: utf-8

# ## Import modules 

# In[ ]:


# !pip install selenium beautifulsoup4 PyPDF requests


# In[204]:


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
import io
import os
from urllib.parse import urlparse, unquote

# Configuration for driver path and agriculture
driver_path = '/Users/nomcebongwamba/Documents/Nomcebo/chromedriver'
agric_directory = '/Users/nomcebongwamba/Documents/Nomcebo/dec_agriculture/txt_fao_koronivia'


# ## Configure Chrome Driver

# In[142]:


""" To launch chromedriver installed with brew, open a terminal and run:
xattr -d com.apple.quarantine $(which chromedriver)
Initialise the Chrome WebDriver
"""
options = webdriver.ChromeOptions()
prefs = { "plugins.always-authorize": True}
options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=options)
driver.implicitly_wait(2)


# ## Crawl webpage for all URLs

# In[147]:


def crawl_webpage(start, end, base_url):
    driver = webdriver.Chrome()
    all_data = []

    for page in range(start, end + 1):
        # Navigate to each page
        driver.get(f"{base_url}?page={page}")
        
        # Wait for the container elements to load on the new page
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".tx-dynalist-pi1-recordlist .list-block")))
        
        # Now collect the container elements for the current page
        containers = driver.find_elements(By.CSS_SELECTOR, ".tx-dynalist-pi1-recordlist .list-block")

        for container in containers:
            # Extract the publication date
            date_elements = container.find_elements(By.CSS_SELECTOR, ".list-date")
            if date_elements:
                date_text = date_elements[1].text if len(date_elements) > 1 else date_elements[0].text
                title_element = container.find_element(By.CSS_SELECTOR, ".list-title a")
                href = title_element.get_attribute('href')
                all_data.append({
                    'publication_type': 'Publication',
                    'date': date_text,
                    'url': href
                })

        # Wait before clicking the next page to avoid rapid requests, if needed
        time.sleep(2)

    # Once complete, close the driver
    driver.quit()
    
    # Print and return the collected data
    for entry in all_data:
        print(entry['publication_type'], entry['date'], entry['url'])
    return all_data


# In[148]:


all_urls = crawl_webpage(1,6, "https://www.fao.org/koronivia/resources/publications/en/")
# with open('/Users/nomcebongwamba/Documents/Nomcebo/dec_agriculture/fao_koronivia_test.txt', 'w') as file:
#     for url in all_urls:
#         file.write(url + '\n')

print("URLs have been saved to fao_agriculture_urls.txt")


# ## Process URLs with no PDFs

# In[152]:


driver = webdriver.Chrome()
def process_urls(publications_url):
    print(len(publications_url))
    
    for publication in publications_url:
        url = publication['url']
        if url.endswith('.pdf'):
            # If the URL already ends with .pdf, add it to the list
            publication['url'] = url
            time.sleep(2)
        else:
            # Open the page for non-.pdf URLs
            driver.get(url)
            time.sleep(2)
            
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

    return publications_url
    driver.quit()
full_urls = process_urls(all_urls)
        
        


# ## Scrape PDF Files

# In[197]:


driver = webdriver.Chrome()

def extract_slug(url):
    parsed_url = urlparse(url)
    slug = unquote(parsed_url.path).strip('/')
    return slug.split('/')[-1]  
def extract_from_html(url):
    driver.get(url)
    title = driver.title
    slug = extract_slug(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    text = ' '.join(p.text for p in soup.find_all('p'))
    return title, slug, text

def extract_from_pdf(url):
    response = requests.get(url)
    file_io = io.BytesIO(response.content)
    reader = PdfReader(file_io)
    meta = reader.metadata
    title = meta.title 
    slug = extract_slug(url)
    text = ''
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text() if page.extract_text() else ''
    return title, slug, text


# In[205]:


for publication in full_urls:
    url = publication['url']
    pub_type = publication['publication_type']
    pub_date = publication['date']
    try:
        if url.endswith('.pdf'):
            title, slug, text = extract_from_pdf(url)
        else:
            title, slug, text = extract_from_html(url)
        output_dir = agric_directory
        os.makedirs(output_dir, exist_ok=True)

        filename = f"{slug}.txt"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Title: {title}\n")
            f.write(f"Slug: {slug}\n")
            f.write(f"URL: {url}\n")
            f.write(f"Type:{pub_type}\n")
            f.write(f"Date: {pub_date}\n")
            f.write("Text:\n")
            f.write(text)

        print(f"Data for {url} written to {filepath}")

    except Exception as e:
        print(f"Error processing {url}: {e}")

