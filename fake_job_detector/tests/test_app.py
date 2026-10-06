"""Integration checks use real bundled models and a temporary history database."""
import csv, io, json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from veritas.server import app
from veritas.samples import SAMPLES
from veritas.engine import indicators
from veritas.signals.security import SecuritySanitizer

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('VERITAS_DB',str(tmp_path/'history.sqlite3'))
    with TestClient(app) as c: yield c

def job(**updates):
    return {**SAMPLES[0]['job'], **updates}

def test_startup_models_and_assets(client):
    assert client.get('/api/health').json()['ready']
    assert 'Job inspector' in client.get('/').text
    assert client.get('/static/app.js').status_code==200
    m=client.get('/api/model-info').json()
    assert m['raw_rows']==17880
    for metrics in m['metrics'].values():
        for split in ['test','validation']:
            tn,fp=metrics[split]['confusion_matrix'][0];fn,tp=metrics[split]['confusion_matrix'][1]
            assert tn+fp+fn+tp==m['splits'][split]['total']
            assert abs(2*tp/(2*tp+fp+fn)-metrics[split]['f1'])<0.00001

def test_analysis_saved_and_review_preserves_prediction(client):
    r=client.post('/api/analyze',json=job()).json()
    assert r['saved'] and len(r['models'])==2
    assert len(client.get('/api/history').json())==1
    reviewed=client.post(f"/api/history/{r['id']}/review",json={'decision':'Concern dismissed','note':'Independent check completed.'})
    assert reviewed.status_code==200
    assert reviewed.json()['risk_score']==r['risk_score']
    assert reviewed.json()['models']==r['models']
    assert reviewed.json()['review']=='Concern dismissed'
    assert client.post(f"/api/history/{r['id']}/review",json={'decision':'Inconclusive','note':'Again'}).status_code==409
    assert client.get(f"/api/history/{r['id']}").json()['review']=='Concern dismissed'

def test_unsaved_and_demo_do_not_write_history(client):
    assert client.post('/api/analyze',json=job(save=False)).json()['saved'] is False
    samples=client.get('/api/samples').json()
    assert len(samples)==5
    for sample in samples:
        r=client.post('/api/demo/'+sample['id'])
        assert r.status_code==200 and not r.json()['saved'] and r.json()['demo']
    assert client.get('/api/history').json()==[]
    assert client.post('/api/demo/missing').status_code==404

@pytest.mark.parametrize('update',[
    {'description':'Too short'}, {'title':''}, {'description':'x'*20001},
    {'application_url':'javascript://alert(1)'}, {'application_url':'https://user:secret@example.com'},
    {'contact_email':'not-an-email'}])
def test_invalid_inputs(client,update):
    assert client.post('/api/analyze',json=job(**update)).status_code==422
    assert client.get('/api/history').json()==[]

def test_batch_partial_success_and_quoted_fields(client):
    s=io.StringIO();w=csv.writer(s);w.writerow(['title','description']);w.writerow(['Engineer, junior',job()['description']]);w.writerow(['Short','bad'])
    r=client.post('/api/batch',files={'file':('jobs.csv',s.getvalue(),'text/csv')})
    assert r.status_code==200
    assert (r.json()['processed'],r.json()['errors'])==(1,1)
    assert r.json()['rows'][0]['result']['job']['title']=='Engineer, junior'
    assert len(client.get('/api/history').json())==1

@pytest.mark.parametrize('data,status',[
    (b'other\nhello',400),(b'title,description\n',400),(b'title,title,description\na,b,c',400),
    (b'\xff\xfe',400),(b'x'*(2*1024*1024+1),413),
    (('title,description\n'+'job,'+'x'*50+'\n').encode()+('job,'+'x'*50+'\n').encode()*100,400)])
def test_invalid_csv(client,data,status):
    assert client.post('/api/batch',files={'file':('jobs.csv',data,'text/csv')}).status_code==status
    assert not client.get('/api/history').json()

def test_payment_credentials_and_negated_warnings():
    codes=lambda text:{x['code'] for x in indicators(job(description=text))['rules']}
    assert 'payment' in codes('Pay a mandatory training fee before receiving an offer.')
    assert 'credentials' in codes('Share your OTP and UPI PIN with the recruiter for verification.')
    assert not codes('We never ask you to pay a training fee. Do not share your OTP.')
    assert 'payment' in codes('We never ask for fees. However, pay a mandatory training fee to proceed.')
    assert 'payment' in codes('No experience required, pay a training fee before joining.')

def test_domains_are_local_rules():
    r=indicators(job(contact_email='careers@a.example',application_url='https://b.example'))
    assert r['domain_score']==30
    r=indicators(job(contact_email='careers@example.com',application_url='https://example.com'))
    assert r['domain_score']==0 and 'Neither ownership nor company registration' in r['domain_notes'][-1]

def test_redaction_keeps_context_and_masks_values(client):
    text='Provide OTP: 123456 and UPI PIN: 4567 to the recruiter. Share your UPI PIN before joining.'
    masked=SecuritySanitizer.mask_pii(text)
    assert '123456' not in masked and '4567' not in masked
    assert 'PIN before joining' in masked
    r=client.post('/api/analyze',json=job(description=text)).json()
    assert '123456' not in json.dumps(r)
    assert 'credentials' in [x['code'] for x in r['signals']['rules']]

def test_split_groups_disjoint():
    root=Path(__file__).resolve().parents[1]
    with (root/'reports/split_membership.csv').open() as f:
        rows=list(csv.DictReader(f))
    group_key=next(k for k in rows[0] if 'group' in k)
    groups={s:{r[group_key] for r in rows if r['split']==s} for s in ['train','validation','test']}
    assert not groups['train'] & groups['test']
    assert not groups['train'] & groups['validation']
    assert not groups['validation'] & groups['test']


def test_advertised_pay_is_not_a_payment_demand():
    r=indicators(job(description='We pay INR 30000 per month for maintaining software services and writing tests.'))
    assert 'payment' not in {x['code'] for x in r['rules']}
