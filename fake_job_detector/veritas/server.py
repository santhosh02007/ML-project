from pathlib import Path
from contextlib import asynccontextmanager
from typing import Literal
import csv,io,json,sqlite3
from fastapi import FastAPI,UploadFile,File,HTTPException
from fastapi.responses import FileResponse,Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field,ConfigDict,field_validator
from veritas.engine import Engine
from veritas.samples import SAMPLES
from veritas import storage
from veritas.signals.security import SecuritySanitizer
ROOT=Path(__file__).resolve().parents[1]
class Job(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True,extra='ignore')
    title:str=Field(min_length=2,max_length=200)
    description:str=Field(min_length=40,max_length=20000)
    company:str=Field(default='',max_length=200)
    location:str=Field(default='',max_length=200)
    requirements:str=Field(default='',max_length=5000)
    benefits:str=Field(default='',max_length=5000)
    company_profile:str=Field(default='',max_length=5000)
    contact_email:str=Field(default='',max_length=254)
    application_url:str=Field(default='',max_length=2000)
    salary:str=Field(default='',max_length=150)
    save:bool=True
    @field_validator('contact_email')
    @classmethod
    def email(cls,v):
      import re
      if v and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',v):raise ValueError('Enter a valid contact email or leave it blank.')
      return v
    @field_validator('application_url')
    @classmethod
    def url(cls,v):
      from urllib.parse import urlsplit
      if v:
        try:
          u=urlsplit(v if '://' in v else 'https://'+v)
          if u.scheme not in ('http','https') or not u.hostname or u.username:raise ValueError()
        except ValueError:raise ValueError('Use an HTTP(S) website address without credentials.')
      return v
class Review(BaseModel):
    decision:Literal['Concern confirmed','Concern dismissed','Inconclusive']
    note:str=Field(min_length=3,max_length=500)
    model_config=ConfigDict(str_strip_whitespace=True)
@asynccontextmanager
async def lifespan(app):
    app.state.engine=Engine()
    with storage.connect():pass
    yield
app=FastAPI(title='Veritas · Fake Job Detector',lifespan=lifespan)
@app.exception_handler(sqlite3.Error)
async def storage_error(request,exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=503,content={'detail':'History could not be saved. Check storage permissions and available disk space.'})
@app.get('/api/health')
def health():return {'ready':hasattr(app.state,'engine'),'version':'2.0'}
@app.get('/api/model-info')
def info():return app.state.engine.metadata
@app.get('/api/samples')
def samples():return SAMPLES

def evaluate(job):
    # Redaction is a limited convenience; it is not a complete PII protection guarantee.
    raw=job.model_dump(exclude={'save'});safe=SecuritySanitizer.sanitize_job_dict(raw)
    result=app.state.engine.analyze(raw)
    # Mask matching numeric secrets in text explanations too.
    def mask(v):
      if isinstance(v,str):return SecuritySanitizer.mask_pii(v)
      if isinstance(v,list):return [mask(x) for x in v]
      if isinstance(v,dict):return {k:mask(x) for k,x in v.items()}
      return v
    return mask(result)|{'job':safe,'saved':False}
@app.post('/api/analyze')
def analyze(job:Job):
    result=evaluate(job)
    if job.save:storage.save_many([result])
    return result
@app.post('/api/demo/{scenario}')
def demo(scenario:str):
    sample=next((s for s in SAMPLES if s['id']==scenario),None)
    if sample is None:raise HTTPException(404,'Scenario not found.')
    return evaluate(Job(**sample['job'],save=False))|{'demo':True,'purpose':sample['purpose']}
@app.get('/api/history')
def history():return storage.history()
@app.get('/api/history/{ident}')
def detail(ident:str):
    r=storage.get(ident)
    if r is None:raise HTTPException(404,'Record not found.')
    return r
@app.post('/api/history/{ident}/review')
def review(ident:str,body:Review):
    try:return storage.review(ident,body.decision,SecuritySanitizer.mask_pii(body.note))
    except KeyError:raise HTTPException(404,'Record not found.')
    except ValueError as e:raise HTTPException(409,str(e))
@app.post('/api/batch')
async def batch(file:UploadFile=File(...)):
    content=await file.read(2*1024*1024+1)
    if len(content)>2*1024*1024:raise HTTPException(413,'Use a CSV smaller than 2 MB.')
    try:
      reader=csv.DictReader(io.StringIO(content.decode('utf-8-sig')),strict=True)
      if not reader.fieldnames or not {'title','description'}<=set(reader.fieldnames):raise HTTPException(400,'CSV requires title and description columns.')
      if len(reader.fieldnames)!=len(set(reader.fieldnames)):raise HTTPException(400,'CSV contains duplicate column names.')
      rows=[]
      for row in reader:
        rows.append(row)
        if len(rows)>100:raise HTTPException(400,'Use at most 100 rows per batch.')
    except (UnicodeDecodeError,csv.Error):raise HTTPException(400,'Use a valid UTF-8 CSV file.')
    if not rows:raise HTTPException(400,'CSV contains no data rows.')
    good=[];output=[]
    for index,row in enumerate(rows,2):
      try:
        if None in row:raise ValueError('Extra cells: quote any commas inside a field.')
        clean={k:(v or '') for k,v in row.items() if k in Job.model_fields and k!='save'}
        job=Job(**clean,save=True);result=evaluate(job);good.append(result);output.append({'row':index,'result':result})
      except (ValueError,TypeError) as e:
        output.append({'row':index,'error':'Check required text lengths, email, URL and CSV quoting.','title':str(row.get('title',''))[:200]})
    if good:storage.save_many(good)
    return {'total':len(rows),'processed':len(good),'errors':len(rows)-len(good),'rows':output}
@app.get('/api/template.csv')
def template():
    s=io.StringIO();w=csv.writer(s);w.writerow(['title','description','company','contact_email','application_url'])
    for sample in SAMPLES[:3]:w.writerow([sample['job'].get(k,'') for k in ['title','description','company','contact_email','application_url']])
    return Response(s.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="sample_jobs.csv"'})
@app.get('/')
def index():return FileResponse(ROOT/'static/index.html')
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
