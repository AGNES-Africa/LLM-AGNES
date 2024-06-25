import os
import datetime
import psycopg2
from datetime import datetime
from utils.existing_category import *
from azure.storage.blob import BlobServiceClient


#Define source id dictionary
source_ids = {
    'staging_ipcc': 1,
    'staging_fao_koronivia-publications': 2,
    'staging_unfccc-decisions': 3,
    'staging_wwf': 4,
    'staging_un_women-publications': 5,
    'staging_gcf': 6,
    'staging_adaptation_fund': 7
}


# Define resource id pattern
resource_patterns = [
    ('staging_ipcc', 'gender', 8),
    ('staging_unfccc', 'agriculture', 2),
    ('staging_fao_koronivia', 'agriculture', 3),
    ('staging_wwf', 'agriculture', 4),
    ('staging_ipcc', 'agriculture', 5),
    ('staging_unfccc', 'gender', 6),
    ('staging_un_women', 'gender', 7),
    ('staging_gcf', 'finance', 9),
    ('staging_adaptation_fund', 'finance', 10),
    ('staging_unfccc', 'finance', 11)
]

def get_ref_id(file_path):
    """
    Get the source ID based on the last directory in the file path.
    
    Args:
    file_path (str): The path of the file.

    Returns:
    int or None: The source ID if found, None otherwise.
    """
    print("file path:", file_path)
    file_path_lower = file_path.lower()
    
    last_directory = os.path.basename(os.path.dirname(file_path)).lower()
    source_id = source_ids.get(last_directory, None)

    # Determine resource ID
    resource_id = None
    for directory, keyword, rid in resource_patterns:
        if directory in last_directory and keyword in file_path_lower:
            resource_id = rid
            # print("resource id:", resource_id)
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


def extract_data_from_file(file_name, blob_client):
    """Extract data fields from the file and determine IDs based on file path."""
    data = {
        'title': None,
        'slug': None,
        'url': None,
        'created_at': None,
        'summary': None,
        'category_name': None,
        'negotiation_stream_id_id': nego_stream_id(file_name),
        'resource_id_id': None,
        'source_id_id': None,
        'category_id_id': None,
        'crawled_at' : get_scraped_datetime()
    }
    
    metadata = blob_client.get_blob_properties().metadata

    # title = metadata.get('Title')
    # if title:
    #     data['title'] = title

    title = metadata.get('Title')
    name = metadata.get('Name')
    if name:
        data['title'] = name + " - " + title
        data['title'] = data['title'][0:200]
        print("title:", data['title'])

    slug = metadata.get('Slug')
    if slug:
        data['slug'] = slug.replace('-', ' ').replace('.pdf', '')

    url = metadata.get('URL')
    if url:
        data['url'] = url

    created_at = metadata.get('Created')
    if created_at:
        data['created_at'] = created_at
    else:
        data['created_at'] = datetime.now().strftime('%Y-%m-%d')

    summary = metadata.get('Summary')
    if summary:
        data['summary'] = summary

    # if title and 'unfccc' in blob_client.blob_name.lower():
    #     data['summary'] = title
    #     data['title'] = name
    # else:
    #     data['summary'] = summary
    #     data['title'] = title
     

    category_name = metadata.get('Category')
    if category_name:
        data['category_name'] = category_name

    return data

def write_to_db(conn, data):
    """Inserts data into the database with negotiation_stream_id_id and source_id_id."""
    try:
        cursor = conn.cursor()
        #This is to ensure that the ids for articles remains sequential
        reset_sequence_query ="""
        SELECT setval('public.Article_Test_id_seq', COALESCE((SELECT MAX(id)+1 FROM public.\"Article_Test\"), 1), false)""" # remember to switch to the app seq id
        # cursor.execute(reset_sequence_query)

        insert_query = """
        INSERT INTO public."Article_Test" ("title", "summary", "slug", "created_at", "url", "negotiation_stream_id_id", "source_id_id","resource_id_id", "category_id_id", "crawled_at") 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
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
            data['category_id_id'],
            data['crawled_at']
        ))
        conn.commit()
        cursor.close()
    except psycopg2.Error as e:
        print(f"Error inserting data into database: {e}")
        conn.rollback()

def process_directory(conn, container_name, connection_string, blob_directory_name):
    """Processes files in a directory, applying specific logic for source_id_id based on subdirectory."""
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    blob_list = container_client.list_blobs(name_starts_with=blob_directory_name)
    print("All blobs found in:", blob_directory_name)

    for blob in blob_list:
        # file_path = os.path.join(subdir, file)
        if blob.name.endswith('.txt'):
            blob_client = container_client.get_blob_client(blob.name)
            data = blob_client.download_blob().readall()
            data = extract_data_from_file(blob.name, blob_client)
            source_id, resource_id = get_ref_id(blob.name)
            category_id, category_name = update_category_table(data, conn, blob.name)
            # print(f"File: {blob.name}, Source ID: {source_id}")
            # print(f"File: {blob.name}, Resource ID: {resource_id}")
            data['source_id_id'] = source_id # Set the source ID based on the directory
            data['resource_id_id'] = resource_id
            data['category_id_id'] = category_id
            data['category_name'] = category_name

            # Retrieve current metadata
            properties = blob_client.get_blob_properties()
            current_metadata = properties.metadata
            current_metadata["Summary"] = data['summary']
            current_metadata["Created"] = data['created_at']

            blob_client.set_blob_metadata(current_metadata)
            # print(data)
            
            # if data['url'] not in urls:
            write_to_db(conn, data) # comment if you want to test
            print(f"{len(data)} rows from {blob.name} written to postgres Article table")
        
            # else:
            #     print("URL already exists in database")
            

            """
            This method retrieves the summary from the blob metadata.
            However, attaching the link with the summary requires concatenating the blob URL with the summary,
            significantly increasing the text field characters.
            This approach requires additional processing, such as ensuring the web app accesses the connection string to return the summary.
            Computationally, this is more expensive than limiting the OpenAI script to summarize the text and return a maximum of 200 characters.
            I recommend using Postgres for storing summaries, which can efficiently handle millions to billions of articles with proper indexing and partitioning.
            """

            # summary_properties = blob_client.get_blob_properties()
            # metadata = summary_properties.metadata
            # summary = metadata.get("Summary")
            