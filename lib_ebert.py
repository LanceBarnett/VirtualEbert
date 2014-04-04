import pickle
import numpy as np
import time

def get_reviews(query, rt):
    '''
    input:  query - movie search term (str)
            rt - instance of RT class (RT)
    output: count - number of movies found (int) 
            title - title of first match (str)
            date_string - Theatrical Release date of first match (str)
            id_list - RottenTomatoes movie ID as list (list)
    '''
    MAX_PAGES = 25
    PAGE_LIMIT = 50
    
    page = 1
    page_count = 0
    total_reviews = 0
    latest_review = ""
    status = 200
    
    title = ''
    date_string = ''
    id_list = []
    review_list = []
    
    movies = rt.search(query,status=status, page_limit=50, page=1)
    #add error handling here
    if (status != 200) or not movies:
        print "Couldn't find any movies"
        count = 0
        return count, title, date_string, id_list, review_list
    movie = movies[0]
    count = len(movies)
    
    id = str(movie['id'])
    id_list.append(id)
    title = movie['title']
    try:
        date_string = movie['release_dates']['theater']
    except KeyError:
        pass
    count_on_this_page = PAGE_LIMIT
    
    
    d = {}
    d['id'] = id
    d['critic'] = 'Fresh'
    if 'critics_score' in movie['ratings']:
        d['original_score'] = str(movie['ratings']['critics_score'])+'/100'
    review_list.append(d)
   # let us loop (and hopefully not hit our rate limit)
    while (count_on_this_page == PAGE_LIMIT) and (page_count < MAX_PAGES):
        if page_count == 4:
            time.sleep(1) # RottenTomatoes rate limits to 5 calls per second
        status = 200
        more_reviews = rt.info(id, status, review_type='all', page_limit=PAGE_LIMIT, page=str(page))
        # make sure it was successful
        if status == 200:
            if more_reviews == []:
                print 'Found nothing on page', page, 'for movie', id
                return count, title, date_string, id_list, review_list
            count_on_this_page = len(more_reviews)
            #print 'Found', count_on_this_page, 'on page', page
            for review in more_reviews:
                total_reviews += 1
                d = review
                d['id'] = id
                review_list.append(d)

                    
                #items_left -= 50
            latest_review = review['critic']
            page += 1
            page_count += 1

        else:
            if status == 403:
                print "Sleepy..."
                # account for rate limiting
                time.sleep(2)
            else:
                print "ERRORS: " + str(status)
                return count, title, date_string, id_list, review_list
    return count, title, date_string, id_list, review_list

def parse_rating(rating_string):
    '''
    Convert ratings text into a score between 0 and 1
    input: (str)
    output: -1 if not parsed; number in [0,1] otherwise (float)
    '''
    score = -1
    x = rating_string.strip("'").split('/')
    if len(x) == 2:
        try:
            ratio = float(x[0])/float(x[1])
            if (ratio >= 0. and ratio <= 1.):
                score = ratio
        except (exceptions.ValueError, exceptions.ZeroDivisionError) as e:
            pass
    return score

def build_matrix(collection, movie_list, critics, fillzeroes=True):
    '''
    Convert data from a list or MongoDB to entries in a (num movies) x (num critics) matrix
    Ratings data ranges from 1 - 9; Missing data is 0 or NaN depending on fillna flag
    input:  collection - list or MongoDB collection (list or )
            movie_list - labels for rows of output matrix (list)
            critics - labels for columns of output matrix (list)
            fillzeros - replace NaNs with zeroes (Boolean)
    '''
    M = np.empty((len(movie_list), len(critics)))
    movie_to_index = dict(zip(movie_list, range(len(movie_list))))
    critic_to_index = dict(zip(critics, range(len(critics))))
    M[:] = np.NaN
    r_count = 0
    if type(collection) is list:
        items = collection
    else:
        items = collection.find()
    for item in items:
        critic = item['critic']
        movie = str(item['id'])
        #print ('original_score' in item), (critic in critic_to_index), (movie in movie_to_index)
        if ('original_score' in item) and (critic in critic_to_index) and (movie in movie_to_index):
            #print "I'm going to parse"
            rating = parse_rating(str(item['original_score']))
            if rating > -1:
                i = movie_to_index[movie]
                j = critic_to_index[critic]
                M[i, j] = rating
                r_count += 1
    M = M*8 + 1 # scores now are integers from 1 - 9
    if fillna:
        M = np.nan_to_num(M)
    print 'Number of entries:', r_count
    print 'Shape of matrix:', np.shape(M)
    return r_count, M
