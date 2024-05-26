
import pandas as pd
from azure.storage.blob import BlobClient
from utils.write_to_blob import *

def update_category_table(data, conn, blob_name):

    # Check if data is a dictionary and convert it to a DataFrame
    if isinstance(data, dict):
        df = pd.DataFrame([data])  # Convert a single dictionary to a DataFrame
    else:
        df = data

    cursor = conn.cursor()
    cursor.execute('SELECT id, trim(lower(title)) as db_title FROM public."Category";')
    existing_categories = cursor.fetchall()
    category_dict = {name: cid for cid, name in existing_categories}


    blob_client = BlobClient.from_connection_string(
    conn_str = connection_string,
    container_name = container_name,
    blob_name=blob_name
    )
    print(blob_name)
    metadata = blob_client.get_blob_properties().metadata
    print(metadata)
    category_name = metadata.get('Category').lower()
    print(category_name)
    for idx, row in df.iterrows():
    #     category_name = row['category_name'].lower().strip()  # Ensure matching format
        if category_name in category_dict:
           df.at[idx, 'category_id'] = category_dict[category_name]
           category_id = df['category_id'].values[0] if not df['category_id'].isnull().all() else None
        else:
            print('Category ID not found')
    return category_id, category_name

    """Next iteration will create a new category id if it does not exist"""
    # # Check if data is a dictionary and convert it to a DataFrame
    # if isinstance(data, dict):
    #     df = pd.DataFrame([data])  # Convert a single dictionary to a DataFrame
    # else:
    #     df = data  # Assume data is already a DataFrame

    # # Continue with the rest of your code
    # cursor = conn.cursor()
    # cursor.execute('SELECT id, trim(lower(title)) as db_title FROM public."Category";')
    # existing_categories = cursor.fetchall()
    # category_dict = {name: cid for cid, name in existing_categories}

    # for idx, row in df.iterrows():
    #     category_name = row['category_name'].lower().strip()  # Ensure matching format

    #     if category_name in category_dict:
    #         df.at[idx, 'category_id'] = category_dict[category_name]
    #         catego
            # cursor.execute(
            #     sql.SQL('INSERT INTO public."Category" (title) VALUES (%s) RETURNING id;'),
            #     [category_name]
            # )
            # category_id = cursor.fetchone()[0]
            # conn.commit()  # Commit after each insert
            
            # # Update dictionary and DataFrame
            # category_dict[category_name] = category_id
            # df.at[idx, 'category_id'] = category_id