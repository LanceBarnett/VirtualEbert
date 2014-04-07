import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import lib_ebert as le
import rottent as RT

# Note: Data files for model not on github but will be part of Yhat deployment
critic_list, sim = pickle.load(open('critic_sim.pkl'))
RF = pickle.load(open('rf_model.pkl'))

from yhat import Yhat, YhatModel , preprocess

class MovieRecommender(YhatModel):
    '''
    Random Forest Recommender as a RESTful API on Yhat
    input: movie search text (str)
    output: Count - number of movies found (int)
            Info - Title and Theatrical Release Date of first movie found (str)
            EbertReviewed - check to see if Ebert actually reviewed this movie (Boolean)
            Great - Prediction of 3.5 or higher rating (Boolean)
            Prob - Model score for Great from 0 - 1 (float)
    '''
    @preprocess(in_type=dict, out_type=dict) 
    def execute(self, data):
        rt=RT.RT()
        movie = data["movie"]
        Ebert = False
        pred = False
        proba = 0
        count, title, date_string, fresh_score, id_list = le.get_movie(rt, str(movie))

        if count > 0:
            total, last_page, review_list = le.get_reviews(rt, id_list[0], fresh_score)
            entries, A = le.build_matrix(review_list, id_list, critic_list, fillzeros=True)
            if entries > 0:
                X_test, y_test = A[:,:-1], A[:,-1]
                Ebert = y_test[0] > 0
                pred = RF.predict(X_test)[0] == 1
                proba = RF.predict_proba(X_test)[0,1]


        result = []
        result.append({"Count" : count})
        result.append({"info": title+' '+date_string})
        result.append({"EbertReviewed" : Ebert})
        result.append({"great": pred})
        result.append({"prob": proba})

        return result