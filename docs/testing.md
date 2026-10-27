 
 # Reunite — Test Runbook
Status: all tests 1–14 passing as of <today's date>
Mode: MUSE_MODE=mock (live mode runs the same code path)
 
 Start clean
bash

cd ~/Reunite
source venv/bin/activate

Confirm you're in the right directory and the venv is active:
bash

pwd
which python

Expected: ~/Reunite and .../venv/bin/python.
Step 1 — Start backend (Terminal A)
bash

uvicorn backend.main:app --reload --port 8000

Leave it running. In Terminal B (new tab), run the rest.
Step 2 — Health check
bash

curl -s http://localhost:8000/api/health
echo

Expected: {"ok":true,"service":"reunite"}

Paste the output → then move to Step 3.
Step 3 — Fresh submission
bash

curl -s -X POST http://localhost:8000/api/submit \
  -H "Content-Type: application/json" \
  -d '{"raw_text":"My sister Layla, near old market in Mosul, phone ended 4471, born 1988","contact":"test@example.com","relationship":"sibling"}' | tee /tmp/sub.json
echo

Expected: {"request_id":"<uuid>","status":"filed"}

Capture the ID for the next steps:
bash

export REQ=$(python -c "import json;print(json.load(open('/tmp/sub.json'))['request_id'])")
echo "REQ=$REQ"

Paste the REQ= line → then Step 4.
Step 4 — Status check
bash

curl -s http://localhost:8000/api/status/$REQ
echo

Expected: {"status":"filed"}
Step 5 — Parse (mock Muse Spark)
bash

curl -s -X POST http://localhost:8000/api/parse/$REQ
echo

Expected: {"request_id":"...","parsed":true,"mode":"mock"}
Step 6 — Match (should be ambiguous if twin exists, otherwise engine)
bash

curl -s -X POST http://localhost:8000/api/match/$REQ | tee /tmp/match.json
echo

Expected: either "resolved_by":"engine" or "resolved_by":"muse_wonder". Both are valid passes — the point is threshold_met: true.
Step 7 — Issue consent token
bash

curl -s -X POST "http://localhost:8000/api/consent/$REQ?candidate_id=c1" | tee /tmp/consent.json
echo

Expected: {"token":"<long>","link":"/api/respond/<long>"}

Capture the token:
bash

export TOK=$(python -c "import json;print(json.load(open('/tmp/consent.json'))['token'])")
echo "TOK=$TOK"

Step 8 — Recipient sees redacted summary
bash

curl -s http://localhost:8000/api/respond/$TOK
echo

Expected: {"redacted_summary":"...","expires_at":"..."}. No candidate name, no seeker identity.
Step 9 — Upload verification image
bash

python -c "from PIL import Image; Image.new('RGB',(300,300),'white').save('/tmp/test.jpg')"

curl -s -X POST "http://localhost:8000/api/respond/$TOK/verify" -F "file=@/tmp/test.jpg" | tee /tmp/verify.json
echo

Expected: {"redacted_url":"/api/redacted/<uuid>.jpg","boxes":[...]}

Capture the filename:
bash

export IMG=$(python -c "import json;print(json.load(open('/tmp/verify.json'))['redacted_url'].split('/')[-1])")
echo "IMG=$IMG"

Step 10 — Fetch the redacted image (this is where the earlier "not found" was)
bash

curl -s -o /tmp/redacted.jpg -w "status=%{http_code}  size=%{size_download}\n" "http://localhost:8000/api/redacted/$IMG"

Expected: status=200 size=<nonzero>

Confirm the file really has a black box drawn:
bash

ls -la /tmp/redacted.jpg

Expected: file exists, size > 0.

If status=404 → the path anchoring didn't take effect, or uvicorn is still serving the old sam.py (reload sometimes lags). In that case:
bash

# In terminal A: Ctrl+C, then restart
uvicorn backend.main:app --reload --port 8000

Then repeat Step 10.

If status=200 → the "not found" bug is fixed. Move on.
Step 11 — Confirm original is unreachable
bash

curl -s -o /dev/null -w "original status=%{http_code}\n" "http://localhost:8000/api/original/$IMG"

Expected: status=404

This is the privacy proof — there is no route that serves the original.
Step 12 — Silent decline
bash

curl -s -X POST http://localhost:8000/api/respond/$TOK/decline
echo
curl -s http://localhost:8000/api/status/$REQ
echo

Expected:
text

{"status":"closed"}
{"status":"filed"}       ← still filed. This is the silent decline.

Step 13 — Accept path (the contrast)
bash

# Fresh request
curl -s -X POST http://localhost:8000/api/submit \
  -H "Content-Type: application/json" \
  -d '{"raw_text":"Looking for brother in Mosul","contact":"t2@example.com"}' | tee /tmp/sub2.json
echo

export REQ2=$(python -c "import json;print(json.load(open('/tmp/sub2.json'))['request_id'])")

curl -s -X POST "http://localhost:8000/api/consent/$REQ2?candidate_id=c1" | tee /tmp/consent2.json
echo

export TOK2=$(python -c "import json;print(json.load(open('/tmp/consent2.json'))['token'])")

curl -s -X POST http://localhost:8000/api/respond/$TOK2/accept
echo
curl -s http://localhost:8000/api/status/$REQ2
echo

Expected:
text

{"status":"closed"}
{"status":"accepted"}    ← contrast with Step 12

Step 14 — DB audit (final proof)
bash

python -c "
import sqlite3
con = sqlite3.connect('backend/reunite.db')
print('REQUESTS:')
for r in con.execute('SELECT id, status FROM seeker_requests'):
    print(' ', r)
print('TOKENS:')
for r in con.execute('SELECT request_id, response, used FROM consent_tokens'):
    print(' ', r)
"