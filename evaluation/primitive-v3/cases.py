"""Gate A: adversarial development cases, never unseen acceptance evidence."""
PREFIX='''import numpy as np
from sklearn.datasets import make_regression
from sklearn.model_selection import KFold, train_test_split
from sklearn.preprocessing import StandardScaler, TargetEncoder
from sklearn.decomposition import PCA, TruncatedSVD, FastICA, NMF
from sklearn.pipeline import make_pipeline
X,y=make_regression(n_samples=40,n_features=4,random_state=19)
X=X*X+1
cv=KFold(n_splits=2)
'''
TRANSFORMERS=['PCA(n_components=2)','TruncatedSVD(n_components=2,random_state=2)','FastICA(n_components=2,random_state=2,max_iter=2000)','NMF(n_components=2,random_state=2,max_iter=2000)','TargetEncoder(target_type="continuous",cv=2,random_state=2)','make_pipeline(PCA(n_components=2),StandardScaler())']
def trace_pairs():
    pairs=[]
    for i,expr in enumerate(TRANSFORMERS,1):
        bad=PREFIX+f'X={expr}.fit_transform(X,y)\nfor a,b in cv.split(X):\n    scaler=StandardScaler()\n    scaler.fit(X[a])\n'
        good=PREFIX+f'for a,b in cv.split(X):\n    transformer={expr}\n    Z=transformer.fit_transform(X[a],y[a])\n'
        if i==5:bad=bad.replace('X=TargetEncoder','Z=TargetEncoder')
        pairs.append((f'transformer-{i}',bad,good))
    holdout=PREFIX+'left,right=train_test_split(X,test_size=0.25,random_state=3)\nscaler=StandardScaler()\nscaler.fit(left)\n'
    pairs.append(('holdout',holdout.replace('scaler.fit(left)','scaler.fit(X)'),holdout))
    nested=PREFIX+'left,right=train_test_split(X,test_size=0.25,random_state=3)\nfor a,b in cv.split(left):\n    scaler=StandardScaler()\n    scaler.fit(left[a])\n'
    pairs.append(('nested',nested.replace('scaler.fit(left[a])','scaler.fit(X)'),nested))
    return pairs
