import os
from dateutil import parser
import re

def reformat_dates(directory, subfolders):
#     subfolders = ['txt_GCF', 'txt_UNFCCC', 'txt_IPCC']
    
    for subfolder in subfolders:
        full_path = os.path.join(directory, subfolder)
        month_year_pattern = re.compile(r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}$')
        
        for filename in os.listdir(full_path):
            if filename.endswith('.txt'):
                file_path = os.path.join(full_path, filename)
                with open(file_path, 'r') as file:
                    lines = file.readlines()
                    
                with open(file_path, 'w') as file:
                    for line in lines:
                        original_line = line 
                        if 'Created: Date:' in line:
                            start_index = line.find('Date:') + 5
                            date_str = line[start_index:].strip()
                        elif line.startswith('Date:'):
                            line = line.replace('Date:', 'Created:')
                            prefix, date_str = line.split('Created:', 1)
                            date_str = date_str.strip()
                        elif line.startswith('Created:'):
                            _, date_str = line.split('Created:', 1)
                            date_str = date_str.strip()
                        else:
                            file.write(line)
                            continue  
                            
                        try:
                            if month_year_pattern.match(date_str):
                                date = parser.parse(date_str)
                                formatted_date = date.strftime('%Y-%m-01')  
                            else:
                                date = parser.parse(date_str, fuzzy=True)
                                formatted_date = date.strftime('%Y-%m-%d')
                            line = f'Created: {formatted_date}\n'
                        except ValueError:
                            line = original_line