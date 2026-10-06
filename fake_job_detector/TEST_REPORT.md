# Release verification

Verified on Linux with Python 3.12, scikit-learn 1.8.0 and the actual bundled model files. This report describes checks performed, not a guarantee that all inputs are classified correctly.

## Automated backend checks: 21 passed

- Server/model startup and frontend assets.
- Confusion-matrix totals and F1 consistency with the measured model metadata.
- Both model predictions returned; local save and record retrieval.
- Human review persistence, completed-review lock and preservation of original model scores.
- Unsaved analyses and all five demos leave history unchanged.
- Invalid title, description, email and URL inputs rejected.
- Valid and invalid rows handled together; quoted CSV fields parsed correctly.
- Missing/duplicate CSV columns, bad encoding, empty files, oversized files and too many rows rejected.
- Payment and credential demands detected; protective wording treated separately; a later payment demand still detected.
- Advertised salary wording is not treated as an upfront fee solely because it mentions pay and INR.
- Domain mismatch rules and explicit non-verification wording.
- Example OTP/PIN value redaction while retaining ordinary sentence context.
- Exact normalized description groups are disjoint across training, validation and test.

Command: `python -m pytest tests -q` from the project folder. The final run reported **21 passed**. A dependency emitted an AnyIO deprecation warning; no test failed.

## Browser checks: passed

Used headless Chromium through Playwright against a running local server, at 1440 × 1080 desktop and 390 × 844 mobile viewport sizes.

- All five scenarios analyzed with the actual models. Observed concern levels: ordinary posting Low; fee request High; OTP request High; anti-scam warning Low; mixed warning and demand High.
- Inspector submission, history details dialog, review saving and close controls worked.
- Batch upload produced one successful row and one validation error; CSV download completed.
- Validation/test metric switch updated displayed values.
- An HTML-like job title rendered as text instead of creating an image element.
- Mobile menu navigation worked and no horizontal page overflow was detected.
- No JavaScript page errors occurred.
- Desktop Inspector, Demo Lab, Model Lab and mobile Inspector screenshots were visually inspected. Reference desktop screenshots are in `docs/screenshots/`.

## Scope not executed here

The Windows `.bat` launchers are included and were reviewed, but this environment cannot run Windows. Dependency setup requires internet access on the user's machine. Native Windows startup, every browser version, the operating system's Print / save PDF dialog, production deployment, load testing and external real-world accuracy were not validated here.
