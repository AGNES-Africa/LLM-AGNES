from psycopg2 import sql
import pandas as pd


def update_category_table(data, conn):
    # Check if data is a dictionary and convert it to a DataFrame
    if isinstance(data, dict):
        df = pd.DataFrame([data])  # Convert a single dictionary to a DataFrame
    else:
        df = data  # Assume data is already a DataFrame

    # Continue with the rest of your code
    cursor = conn.cursor()
    cursor.execute('SELECT id, trim(lower(title)) as db_title FROM public."Category";')
    existing_categories = cursor.fetchall()
    category_dict = {name: cid for cid, name in existing_categories}

    for idx, row in df.iterrows():
        category_name = row['category_name'].lower().strip()  # Ensure matching format

        if category_name in category_dict:
            df.at[idx, 'category_id'] = category_dict[category_name]
            category_id = df['category_id'].values[0] if not df['category_id'].isnull().all() else None
        else:
            print('Category ID not found')
            """Next iteration will create a new category id if it does not exist"""


            
            # cursor.execute(
            #     sql.SQL('INSERT INTO public."Category" (title) VALUES (%s) RETURNING id;'),
            #     [category_name]
            # )
            # category_id = cursor.fetchone()[0]
            # conn.commit()  # Commit after each insert
            
            # # Update dictionary and DataFrame
            # category_dict[category_name] = category_id
            # df.at[idx, 'category_id'] = category_id

    return category_id, category_name