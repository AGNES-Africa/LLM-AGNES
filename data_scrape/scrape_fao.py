#!/usr/bin/env python
# coding: utf-8

# ## Scrape the website for PDF files

# In[ ]:


# !pip install selenium beautifulsoup4 PyPDF requests


# In[84]:


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
agric_directory = '/Users/nomcebongwamba/Documents/Nomcebo/dec_agriculture/txt_dec_agriculture'


# In[44]:


""" To launch chromedriver installed with brew, open a terminal and run:
xattr -d com.apple.quarantine $(which chromedriver)
Initialise the Chrome WebDriver
"""
options = webdriver.ChromeOptions()
prefs = { "plugins.always-authorize": True}
options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=options)
driver.implicitly_wait(2)


# In[45]:


driver.get("https://www.fao.org/common-pages/search/en/?q=agriculture+and+climate+change")
time.sleep(5) 


# ## Crawl webpage

# In[46]:


"""
1. Initialise an empty set for urls
2. Iterate over first page, add links to set
3. Navigate to next page, continue with step 2
4. Once complete close the driver
"""


def crawl_webpage(start, end):
    all_urls = set()
    for page in range(start, end):
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href]")))

        links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
        for link in links:
            href = link.get_attribute('href')
            if href:
                all_urls.add(href)

        if page < 10:
            next_page_aria_label = f"Page {page + 1}"
            next_page_selector = f"div.gsc-cursor-page[aria-label='{next_page_aria_label}']"
            next_page = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, next_page_selector)))
            next_page.click()

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href]")))
            time.sleep(2)

    for url in all_urls:
        print(url)
    return all_urls





# In[47]:


all_urls = crawl_webpage(1,11)
with open('/Users/nomcebongwamba/Documents/Nomcebo/dec_agriculture/fao_agriculture_urls.txt', 'w') as file:
    for url in all_urls:
        file.write(url + '\n')

print("URLs have been saved to fao_agriculture_urls.txt")


# In[48]:


len(all_urls)


# In[49]:


driver.quit()


# ## Scrape PDF Files

# In[61]:





# In[85]:


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


# In[ ]:


for url in all_urls:
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
            f.write("Text:\n")
            f.write(text)
        
        print(f"Data for {url} written to {filepath}")
    
    except Exception as e:
        print(f"Error processing {url}: {e}")

