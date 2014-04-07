import exceptions
import pandas as pd
from pymongo import MongoClient
from pymongo import errors
import rottent as RT
import lib_ebert as le


# Functions used to get and store critic reviews from Rotten Tomato movie ids

def scrape_reviews(df, collection, starting_row=0):
    '''
    Iterate over movie ids in dataframe and write reviews to a Mongo collection
    Dataframe will be updated in place with progress on the scraping
    Input/Output:   df (Pandas Dataframe)
                    collection (Mongo collection)
                    starting_row - if restarting set to first unscraped row (int)
    '''
    rt = RT.RT()
    for index, row in df[starting_row:].iterrows():
        if index%50 == 0:
            print 'Scraping movie:', index
        m_id = df['movie_id'][index]
        m_fresh = df['freshness'][index]
        m_fresh = m_fresh.strip().strip('%')
        total_stated, final_page, review_list = le.get_reviews(rt, m_id, m_fresh)
        add_to_mongo(review_list, collection)
        total_items = len(review_list)
        if total_stated < total_items-1:
            print 'For', m_id, 'found', total_items, 'out of', total_stated
        df['total'][index] = total_stated
        df['found'][index] = total_items
        df['pages'][index] = final_page

def add_to_mongo(list_of_docs, collection):
    '''
    Add reviews to Mongo collection
    input:  list_of_docs - each dictionary in this list added as a doc (list)
            collection - MongoDB collection
    '''
    try:
        collection.insert(list_of_docs, continue_on_error=True)
    except errors.DuplicateKeyError:
        pass
  
