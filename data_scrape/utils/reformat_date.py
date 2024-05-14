import os
from dateutil import parser
import re

def reformat_date(date):
    month_year_pattern = re.compile(r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}$')                            
    try:
        if month_year_pattern.match(date):
            date = parser.parse(date)
            formatted_date = date.strftime('%Y-%m-01')  
        else:
            date = parser.parse(date, fuzzy=True)
            formatted_date = date.strftime('%Y-%m-%d')
            print(f'Created: {formatted_date}\n')
            return formatted_date
    except:
        print("Could not format date")
        return date