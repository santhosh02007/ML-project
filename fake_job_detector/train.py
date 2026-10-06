"""Train reproducibly. Select model/threshold on validation; evaluate on test once."""
from pathlib import Path
import hashlib, json, time, platform
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import sklearn, joblib
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, average_precision_score, roc_auc_score, confusion_matrix
from veritas.text import combined, clean
ROOT = Path(__file__).resolve().parent

def metrics(y, p, threshold):
    pred = p >= threshold
    return {k: round(float(v), 5) for k,v in {
        'precision':precision_score(y,pred,zero_division=0), 'recall':recall_score(y,pred,zero_division=0),
        'f1':f1_score(y,pred,zero_division=0), 'accuracy':accuracy_score(y,pred),
        'average_precision':average_precision_score(y,p), 'roc_auc':roc_auc_score(y,p)}.items()} | {'confusion_matrix':confusion_matrix(y,pred,labels=[0,1]).tolist()}

def main():
    start=time.time(); path=ROOT/'data/fake_job_postings.csv'
    df=pd.read_csv(path).fillna(''); raw_rows=len(df)
    if set(df.fraudulent.unique()) != {0,1}:raise ValueError('Expected binary fraudulent labels')
    df['text']=df.apply(lambda row:combined(row.to_dict()),axis=1)
    df=df[df.text.str.len()>20].copy()
    # Remove conflicting labels for identical input and duplicate full inputs.
    conflicts=df.groupby('text').fraudulent.nunique(); bad=set(conflicts[conflicts>1].index)
    df=df[~df.text.isin(bad)].drop_duplicates('text').reset_index(drop=True)
    groups=df.description.map(clean);groups=groups.where(groups.str.len()>0,df.text)
    y=df.fraudulent.to_numpy(dtype=int)
    outer=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=42)
    trainval,test=next(outer.split(df.text,y,groups))
    inner=StratifiedGroupKFold(n_splits=4,shuffle=True,random_state=43)
    ti,vi=next(inner.split(df.text.iloc[trainval],y[trainval],groups.iloc[trainval]))
    train,val=trainval[ti],trainval[vi]
    for a,b in [(train,val),(train,test),(val,test)]:assert not set(groups.iloc[a])&set(groups.iloc[b])
    vectorizer=TfidfVectorizer(max_features=20000,ngram_range=(1,2),min_df=2,sublinear_tf=True,dtype=np.float32)
    Xtrain=vectorizer.fit_transform(df.text.iloc[train]);Xval=vectorizer.transform(df.text.iloc[val]);Xtest=vectorizer.transform(df.text.iloc[test])
    models={'logistic_regression':LogisticRegression(class_weight='balanced',C=2,max_iter=1000,random_state=42,solver='liblinear'),
            'random_forest':RandomForestClassifier(n_estimators=180,class_weight='balanced',max_features='sqrt',min_samples_leaf=1,n_jobs=2,random_state=42)}
    evaluation={};thresholds={}
    for name,model in models.items():
        print('Training',name,flush=True);model.fit(Xtrain,y[train]);vp=model.predict_proba(Xval)[:,1]
        candidates=np.arange(.1,.81,.05)
        threshold=float(max(candidates,key=lambda t:(f1_score(y[val],vp>=t,zero_division=0),recall_score(y[val],vp>=t,zero_division=0))))
        thresholds[name]=round(threshold,3)
        evaluation[name]={'threshold':thresholds[name],'validation':metrics(y[val],vp,threshold),'test':metrics(y[test],model.predict_proba(Xtest)[:,1],threshold)}
        print(name,evaluation[name],flush=True)
    champion=max(models,key=lambda name:evaluation[name]['validation']['f1'])
    split=lambda ids:{'total':len(ids),'fraud':int(y[ids].sum()),'genuine':int((y[ids]==0).sum())}
    metadata={'version':'2.0','trained_at':datetime.now(timezone.utc).isoformat(),'dataset':'Kaggle / EMSCAD real and fake job postings','source':json.loads((ROOT/'data/provenance.json').read_text()),'raw_rows':raw_rows,'usable_rows':len(df),'removed_rows':raw_rows-len(df),'conflicting_input_groups_removed':len(bad),'unique_descriptions':int(groups.nunique()),'splits':{'train':split(train),'validation':split(val),'test':split(test)},'method':'Stratified group splits using normalized description. Approx. 60/20/20; actual sizes shown. TF-IDF fitted only on training. Balanced class weights. Threshold and champion selected only on validation F1. No oversampling.', 'leakage_check':{'identical_description_group_overlap':0,'note':'Exact normalized description groups do not cross splits. This does not exclude all near-duplicate/company overlap.'},'champion':champion,'metrics':evaluation,'sklearn_version':sklearn.__version__,'python_version':platform.python_version(),'features':len(vectorizer.vocabulary_),'elapsed_seconds':round(time.time()-start,2),'limitations':'Historical English job-posting data; test scores describe this held-out sample, not current-world guarantees. Hybrid rule scores are not calibrated probabilities.'}
    (ROOT/'models').mkdir(exist_ok=True)
    joblib.dump({'vectorizer':vectorizer,'models':models,'thresholds':thresholds,'champion':champion},ROOT/'models/bundle.joblib',compress=3)
    (ROOT/'models/metrics.json').write_text(json.dumps(metadata,indent=2))
    # IDs document membership without repeating all text.
    membership=[]
    for label,ids in [('train',train),('validation',val),('test',test)]:
        membership.extend({'job_id':int(df.iloc[i].job_id),'split':label,'group_sha256':hashlib.sha256(groups.iloc[i].encode()).hexdigest()} for i in ids)
    pd.DataFrame(membership).to_csv(ROOT/'reports/split_membership.csv',index=False)
    print('Complete:',champion,'seconds',metadata['elapsed_seconds'],flush=True)
if __name__=='__main__':main()
