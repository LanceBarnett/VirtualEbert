import numpy as np
from scipy.stats import pearsonr

# Functions used for building collaborative filter models

def filter_arrays(a, b):
    '''
    input: a,b - 1-D arrays of floats with positive-valued data
    output: same arrays restricted to coordinates with data in both arrays
    '''
    index = [i for i in range(len(a)) if a[i]>0 and b[i]>0]
    if not index:
        return None, None
    return a[index], b[index]

def get_pearsonr(X, y, filter=True):
    '''
    input:  X - array of critic ratings (num movies x num critics)
            y - array of Ebert ratings (num movies x 1)
    output: similarity array (num critics x 1)
    '''
    sim = np.zeros(len(X.T))
    for i in range(len(X.T)):
        a, b = X[:,i], y
        if filter:
            a, b = filter_arrays(X[:,i], y)
        if a != None:
            sim[i], p = pearsonr(a, b)
    if sim.min() < 0:
        sim = sim - sim.min() + .001 # want similarity to be bounded away zero
    return np.nan_to_num(sim)

def predict(X, similarity):
    '''
    Predictions of movie ratings based on similarity.
    input: X (num movies x num critics), similarity (num critics x 1)
    output: Y (num movies x 1)
    '''
    X_binary = np.where(X==0, 0, 1)
    totals_vector = X_binary.dot(similarity)
    if totals_vector.min() == 0:
        # Sparse data may lead to some zeros; just need to bound totals away from zero 
        totals_vector = totals_vector + .001
    Y = X.dot(similarity)/totals_vector

    return Y

def base_predict(X):
    '''
    Base case collaborative filter - just use average ratings
    input: X (num movies x num critics)
    output: Y (num movies x 1)
    '''
    X_binary = np.where(X==0, 0, 1)
    One_vector = np.ones((len(X.T),1))
    totals_vector = X_binary.dot(One_vector)
    Y = X.dot(One_vector)/totals_vector
    return Y

def closest_predict(X, similarity):
    '''
    Another comparative collaborative filter - just use best rating available
    input: X (num movies x num critics), similarity (num critics x 1)
    output: Y (num movies x 1)
    '''
    index = similarity.argsort(axis=0)[::-1]
    
    Y = np.zeros((len(X), 1))
    chosen = np.zeros((len(X), 1))
    for j in range(len(index)):
        for row in range(len(X)):
            if Y[row, 0] == 0:
                Y[row, 0] = X[row, index[j]]
                chosen[row, 0] = index[j]
    return Y, chosen  

def bin_classify(A, cutoff=8):
    '''
    Convert Ebert ratings or predictions to binary categories
    input:  A - ratings that have been scaled to 1-9 inclusive (numpy array)
            cutoff - default of 8, i.e. 3.5/4 stars (float)
    output: A_class - binary classification for A (numpy array)
    '''
    A_class = np.array(map(lambda x: 1 if x>=cutoff else 0, A))
    return A_class

