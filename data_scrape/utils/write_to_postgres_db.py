import os
import datetime
import psycopg2
from datetime import datetime
from utils.existing_category import *


#Define source id dictionary
source_ids = {
    'txt_ipcc': 1,
    'txt_fao_koronivia': 2,
    'txt_unfccc': 3,
    'txt_wwf': 4,
    'txt_un_women': 5,
    'txt_gcf': 6,
    'txt_adaptation_fund': 7
}


# Define resource id pattern
resource_patterns = [
    ('txt_ipcc', 'gender', 8),
    ('txt_unfccc', 'agriculture', 2),
    ('txt_fao_koronivia', 'agriculture', 3),
    ('txt_wwf', 'agriculture', 4),
    ('txt_ipcc', 'agriculture', 5),
    ('txt_unfccc', 'gender', 6),
    ('txt_un_women', 'gender', 7),
    ('txt_gcf', 'finance', 9),
    ('txt_adaptation_fund', 'finance', 10),
    ('txt_unfccc', 'finance', 11)
]

def get_ref_id(file_path):
    """
    Get the source ID based on the last directory in the file path.
    
    Args:
    file_path (str): The path of the file.

    Returns:
    int or None: The source ID if found, None otherwise.
    """
    file_path_lower = file_path.lower()
    last_directory = os.path.basename(os.path.dirname(file_path)).lower()
    source_id = source_ids.get(last_directory, None)

    # Determine resource ID
    resource_id = None
    for directory, keyword, rid in resource_patterns:
        if directory in last_directory and keyword in file_path_lower:
            resource_id = rid
            break

    return (source_id, resource_id)


def nego_stream_id(file_path):
    lower_path = file_path.lower()
    if 'gender' in lower_path:
        return 2  
    elif 'finance' in lower_path:
        return 3  
    elif 'agriculture' in lower_path:
        return 1  
    else:
        return None
def get_scraped_datetime():
    scraped_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return scraped_datetime


def extract_data_from_file(file_path):
    """Extract data fields from the file and determine IDs based on file path."""
    data = {
        'title': None,
        'slug': None,
        'url': None,
        'created_at': None,
        'summary': None,
        'category_name': None,
        'negotiation_stream_id_id': nego_stream_id(file_path),
        'resource_id_id': None,
        'source_id_id': None,
        'category_id_id': None,
        'scraped_at' : get_scraped_datetime()
    }
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('Title:'):
                title = line.strip().split('Title:', 1)[1].strip()
            elif line.startswith('Name:') and 'unfccc' in file_path.lower():
                data['title'] = line.strip().split('Name:', 1)[1].strip()
            elif line.startswith('Slug:'):
                data['slug'] = line.strip().split('Slug:', 1)[1].strip().replace('-', ' ').replace('.pdf', '')
            elif line.startswith('URL:'):
                data['url'] = line.strip().split('URL:', 1)[1].strip()
            elif line.startswith('Created:'):
                data['created_at'] = line.strip().split('Created:', 1)[1].strip()
            elif line.startswith('Summary:'):
                summary = line.strip().split('Summary:', 1)[1].strip()
            elif line.startswith('Category:'):
                data['category_name'] = line.strip().split('Category:', 1)[1].strip()

        # Apply the condition for unfccc files processing logic based on file_path
        if 'unfccc' in file_path.lower():
            if 'title' in locals():
                data['summary'] = title
        else:
            if 'title' in locals():
                data['title'] = title
            if 'summary' in locals():
                data['summary'] = summary
    if not data['created_at']:
        data['created_at'] = datetime.now().strftime('%Y-%m-%d')
    return data

def write_to_db(conn, data):
    """Inserts data into the database with negotiation_stream_id_id and source_id_id."""
    try:
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO public."Article2" ("title", "summary", "slug", "created_at", "url", "negotiation_stream_id_id", "source_id_id","resource_id_id", "scraped_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (
            data['title'],
            data['summary'],
            data['slug'],
            data['created_at'],
            data['url'],
            data['negotiation_stream_id_id'],
            data['source_id_id'],
            data['resource_id_id'],
            data['scraped_at']
        ))
        conn.commit()
        cursor.close()
    except psycopg2.Error as e:
        print(f"Error inserting data into database: {e}")
        conn.rollback()

def process_directory(directory, urls, conn):
    """Processes files in a directory, applying specific logic for source_id_id based on subdirectory."""
    for subdir, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(subdir, file)
                data = extract_data_from_file(file_path)
                file_path = os.path.join(subdir, file)
                source_id, resource_id = get_ref_id(file_path)
                category_id, category_name = update_category_table(data, conn)
                print(f"File: {file}, Source ID: {source_id}")
                print(f"File: {file}, Resource ID: {resource_id}")
                data['source_id_id'] = source_id # Set the source ID based on the directory
                data['resource_id_id'] = resource_id
                data['category_id_id'] = category_id.astype(int)
                data['category_name'] = category_name
                # if data['url'] not in urls:
                    # print(data['category_id_id'])
                print(data)
                    # write_to_db(conn, data) # uncomment if you want to write to the database
                # else:
                #     print("URL already exists in database")