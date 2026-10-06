"""ML inference plus explicitly labelled, local heuristic checks."""
from pathlib import Path
import json, re, time, html
from urllib.parse import urlsplit
import joblib
import numpy as np
from veritas.text import combined
ROOT=Path(__file__).resolve().parents[1]
NAMES={'logistic_regression':'Logistic Regression','random_forest':'Random Forest'}

def indicators(job):
    raw='\n'.join(str(job.get(k,'') or '') for k in ['title','description','requirements','benefits'])
    raw=html.unescape(re.sub(r'<[^>]*>',' ',raw))
    # Clause-scoped negation: a warning must not hide a later positive demand.
    clauses=re.split(r'[.!?;,\n]|\bbut\b|\bhowever\b|\byet\b',raw,flags=re.I)
    rules=[
      ('payment','Upfront payment',45,r'\b(?:pay|send|transfer|deposit|mandatory|required|refundable|joining)\b.{0,65}\b(?:fee|fees|deposit|payment)\b|\b(?:security|equipment|laptop|registration|training)\s+(?:deposit|fee)\b|joining fee kattavum|deposit seiyavum'),
      ('credentials','Sensitive information request',70,r'\b(?:send|share|provide|submit|verify|verification|required)\b.{0,70}\b(?:otp|upi pin|banking password|bank password|cvv|card number)\b|\b(?:otp|upi pin|banking password|cvv)\b.{0,40}\b(?:required|send|share|verification)\b'),
      ('check','Check or transfer arrangement',55,r'cashier.?s? check|wire.{0,30}(?:remaining|excess|funds)|(?:deposit|cash).{0,25}check.{0,60}(?:vendor|equipment|send|transfer)|crypto deposit'),
      ('pressure','Pressure or guaranteed earnings',25,r'guaranteed (?:income|earnings|daily payout)|start today without interview|limited slots.{0,15}act fast|instant joining letter'),
      ('chat','Messaging-only recruitment',20,r'interview (?:via|on) telegram|whatsapp interview only|contact (?:hr|recruiter|manager) on (?:telegram|whatsapp)'),
    ]
    findings=[];disclaimers=[]
    negative=re.compile(r"\b(?:never|not|no|don't|do not|without|beware|warning|avoid)\b",re.I)
    for code,label,weight,pattern in rules:
      hits=[]
      for clause in clauses:
        m=re.search(pattern,clause,re.I)
        if m:
          if negative.search(clause[:m.end()]):disclaimers.append(clause.strip());continue
          hits.append(clause.strip()[:220])
      if hits:findings.append({'code':code,'label':label,'weight':weight,'detail':'Review this wording in its full context.','evidence':list(dict.fromkeys(hits))[:3]})
    # Explicit warnings also shown when there are no trigger matches.
    for clause in clauses:
      if re.search(r'\b(?:never|do not|no)\b.{0,55}\b(?:fee|fees|payment|deposit|otp)\b',clause,re.I):disclaimers.append(clause.strip())
    email=(job.get('contact_email') or '').strip().lower();url=(job.get('application_url') or '').strip()
    host='';domain=email.rsplit('@',1)[-1] if '@' in email else ''
    if url:
      try:host=(urlsplit(url if '://' in url else 'https://'+url).hostname or '').lower().removeprefix('www.')
      except ValueError:pass
    domain_points=0;domain_notes=[]
    if url.startswith('http://'):domain_points+=15;domain_notes.append('The supplied link uses HTTP rather than HTTPS.')
    if url and (not host or re.fullmatch(r'[\d.]+',host)):domain_points+=25;domain_notes.append('The URL has a missing host or a numeric IP host.')
    if domain in {'gmail.com','yahoo.com','outlook.com','hotmail.com','protonmail.com'}:
      domain_points+=15;domain_notes.append('The contact uses public webmail. This alone does not establish fraud.')
    if domain and host and not (domain==host or domain.endswith('.'+host) or host.endswith('.'+domain)):
      domain_points+=30;domain_notes.append('The supplied email and website domains differ. Third-party recruiters may need a separate check.')
    if not domain_notes:domain_notes.append('No domain mismatch rule fired.' if domain and host else 'Email or website information is missing; this check is incomplete.')
    if domain and host and domain==host:domain_notes.append('The two supplied domains match. Neither ownership nor company registration has been verified.')
    # Salary is only flagged for explicit, narrow currency/period combinations.
    salary=job.get('salary','');salary_notes=[];salary_points=0
    if salary:
      s=salary.lower().replace(',','');m=re.search(r'(?:₹|rs\.?|inr)\s*(\d+(?:\.\d+)?)\s*(?:/|per\s*)day',s)
      usd=re.search(r'\$\s*(\d+(?:\.\d+)?)\s*(?:/|per\s*)(?:hour|hr)',s)
      routine=bool(re.search(r'data entry|typing|typist|clerk',job['title'],re.I))
      if routine and ((m and float(m[1])>5000) or (usd and float(usd[1])>60)):
        salary_points=25;salary_notes.append('Pay exceeds the project’s illustrative threshold for a routine role. This is a heuristic, not a market salary assessment.')
      else:salary_notes.append('No supported salary rule fired. No general salary verification was performed.')
    return {'rules':findings,'rule_score':min(100,sum(x['weight'] for x in findings)), 'disclaimers':list(dict.fromkeys(disclaimers)), 'domain_score':min(100,domain_points),'domain_notes':domain_notes,'salary_score':salary_points,'salary_notes':salary_notes,'email_domain':domain,'website_domain':host}

class Engine:
    def __init__(self):
        path=ROOT/'models/bundle.joblib'
        if not path.exists():raise RuntimeError('Trained models are missing. Restore the complete ZIP or run train.py.')
        self.bundle=joblib.load(path)
        self.metadata=json.loads((ROOT/'models/metrics.json').read_text())
        self.words=np.array(self.bundle['vectorizer'].get_feature_names_out())
    def analyze(self,job):
        start=time.perf_counter();X=self.bundle['vectorizer'].transform([combined(job)])
        comparison=[]
        for key,model in self.bundle['models'].items():
            score=float(model.predict_proba(X)[0,1]);threshold=self.bundle['thresholds'][key]
            comparison.append({'key':key,'name':NAMES[key],'score':round(score*100,2),'threshold':threshold*100,'flagged':score>=threshold,'champion':key==self.bundle['champion']})
        chosen=next(m for m in comparison if m['champion']);signals=indicators(job)
        risk=round(.65*chosen['score']+.25*signals['rule_score']+.1*signals['domain_score']+signals['salary_score']*.2)
        if chosen['flagged']:risk=max(risk,61)
        codes={r['code'] for r in signals['rules']}
        if codes&{'credentials','check'} or signals['rule_score']>=70:risk=max(risk,80)
        elif 'payment' in codes:risk=max(risk,65)
        elif signals['rule_score'] or signals['domain_score']>=30:risk=max(risk,35)
        risk=min(100,risk);level='High' if risk>=61 else 'Medium' if risk>=31 else 'Low'
        coefs=self.bundle['models']['logistic_regression'].coef_[0];weights=[(str(self.words[i]),float(X[0,i]*coefs[i])) for i in X.indices]
        positive=sorted([w for w in weights if w[1]>0],key=lambda w:-w[1])[:6]
        negative=sorted([w for w in weights if w[1]<0],key=lambda w:w[1])[:6]
        return {'risk_score':risk,'risk_level':level,'verdict':{'High':'High concern','Medium':'Review recommended','Low':'Lower concern'}[level],
          'recommendation':{'High':'Pause before sending money or personal information. Independently contact the employer through a trusted channel.','Medium':'Check the highlighted details and independently confirm the recruiter before proceeding.','Low':'Fewer warning signals were found. This does not verify the employer or guarantee that the job is genuine.'}[level],
          'models':comparison,'signals':signals,'explanation':{'model':'Logistic Regression','toward_fraud':[{'term':t,'weight':round(w,4)} for t,w in positive],'toward_genuine':[{'term':t,'weight':round(w,4)} for t,w in negative],'note':'These are signed TF-IDF × coefficient contributions to the LR log-odds, not explanations of the Random Forest.'},
          'vocabulary_terms':int(X.nnz),'model_version':self.metadata['version'],'analysis_ms':round((time.perf_counter()-start)*1000,1),
          'notice':'Model scores and combined risk index are estimates, not verified probabilities or proof of fraud. Domain checks are local rules; no company registry or website was contacted.'}
