"""One shared text pipeline for training and prediction."""
import html
import re
FIELDS = ('title', 'company_profile', 'description', 'requirements', 'benefits', 'location')
def clean(value):
    value = html.unescape(str(value or ''))
    value = re.sub(r'<[^>]*>', ' ', value).lower()
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', value)).strip()
def combined(job):
    return ' '.join(clean(job.get(field, '')) for field in FIELDS).strip()
