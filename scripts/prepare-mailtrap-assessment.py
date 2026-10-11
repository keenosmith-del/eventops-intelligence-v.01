"""Insert three controlled messages only into the existing fixed testing sandbox.

Explicit --submit required; never uses transactional/bulk email endpoints.
Loads existing local credentials, without modifying .env or printing secrets.
"""
import argparse
import json
import os
from pathlib import Path
import httpx
from dotenv import load_dotenv

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--submit', action='store_true')
args = parser.parse_args()
payloads = json.loads((root / 'docs/testing/mailtrap/final-assessment.json').read_text())
if not args.submit:
    print('Prepared positive, duplicate and inactive-conflict messages; use --submit for the authorized fixed sandbox.')
    raise SystemExit(0)
load_dotenv(root / '.env', override=False)
if (os.getenv('MAILTRAP_ACCOUNT_ID'), os.getenv('MAILTRAP_INBOX_ID')) != ('2853336', '4953522'):
    raise SystemExit('Configured IDs do not match the authorized assessment sandbox.')
token = os.getenv('MAILTRAP_API_TOKEN')
if not token:
    raise SystemExit('Existing sandbox token is missing.')
with httpx.Client(timeout=httpx.Timeout(12, connect=5), follow_redirects=False) as client:
    for index, payload in enumerate(payloads, 1):
        try:
            response = client.post('https://sandbox.api.mailtrap.io/api/send/4953522', headers={'Api-Token': token}, json=payload)
            if response.status_code != 200 or response.json().get('success') is not True:
                raise SystemExit(f'Sandbox message {index}: HTTP {response.status_code}, insertion not confirmed. No retry; inspect the sandbox before resubmission.')
        except (httpx.HTTPError, ValueError):
            raise SystemExit(f'Sandbox message {index}: insertion could not be confirmed. No retry; inspect inbox before resubmission.') from None
        print(f'Sandbox message {index}: insertion confirmed; synthetic testing inbox only.')
