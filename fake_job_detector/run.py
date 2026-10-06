"""Single-server launcher. No frontend build or external API is needed."""
from pathlib import Path
import os
os.chdir(Path(__file__).resolve().parent)
if __name__=='__main__':
    import uvicorn
    print('Open http://127.0.0.1:8000 after the startup message. Press Ctrl+C to stop.')
    uvicorn.run('veritas.server:app',host='127.0.0.1',port=int(os.environ.get('PORT','8000')))
