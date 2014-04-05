import exceptions
import pandas as pd

# Functions used to get critic reviews from Rotten Tomato movie ids

def get_movie_reviews(df, collection):
    '''
    Iterate over movie ids in dataframe and write reviews to a Mongo collection
    Dataframe will be updated in place with progress on the scraping
    Input/Output:   df (Pandas Dataframe)
                    collection (Mongo collection)
    '''
    for index, row in df[:].iterrows():
        if index%50 == 0:
            print 'Scraping movie:', index
        m_id = df['movie_id'][index]
        status, total_stated, total_items, final_page, latest_item = scrape_reviews(m_id, collection)
        if total_stated != total_items:
            print 'For', m_id, 'found', total_items, 'out of', total_stated
        df['status'][index] = status
        df['total'][index] = total_stated
        df['found'][index] = total_items
        df['pages'][index] = final_page
        df['last'][index] = latest_item

def scrape_reviews(id, collection):
    '''
    Add reviews to Mongo collection
    input:  id - RottenTomatoes movie id code (str)
            collection - MongoDB collection
    output: status - http status (int) 
            total_stated - number of reviews as reported by RottenTomatoes (int)
            total_items - actual number of reviews found (int)
            final_page - number of review pages collected (int)
            latest_item - name of last critic review for id loaded to collection (str)
    '''

    MAX_PAGES = 25
    PAGE_LIMIT = 50
    
    final_page = 1
    page = 1
    page_count = 0
    total_items = 0
    latest_item = ""
    
    id = str(id)

    rt = RT()
    count_on_this_page = PAGE_LIMIT
    
    # let us loop (and hopefully not hit our rate limit)
    while (count_on_this_page == PAGE_LIMIT) and (page_count < MAX_PAGES):
        status = 200
        total_stated, more_items = rt.info(id, status, review_type='all', page_limit=PAGE_LIMIT, page=str(page))
        # make sure it was successful
        if status == 200:
            if more_items == []:
                print 'Found nothing on page', page, 'for movie', id
                return status, total_stated, total_items, final_page, latest_item
            count_on_this_page = len(more_items)
            #print 'Found', count_on_this_page, 'on page', page
            for item in more_items:
                total_items += 1
                dict = item
                dict['id'] = id
                
                if not collection.find_one(dict):
                    #print "No dups"
                    try:
                        #print "Inserting item", id, item['critic']
                        collection.insert(dict)
                    except errors.DuplicateKeyError:
                        #print "Duplicates"
                        continue
                else:
                    print "In collection already:", id, item['critic']

                    
                #items_left -= 50
            latest_item = item['critic']
            page += 1
            page_count += 1
            final_page = page_count
        else:
            if status == 403:
                print "Sleepy..."
                # account for rate limiting
                time.sleep(2)
            else:
                print "ERRORS: " + str(status)
                return status, total_stated, total_items, final_page, latest_item
    return status, total_stated, total_items, final_page, latest_item

