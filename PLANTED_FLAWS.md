# SPOILERS: planted flaws

Don't read this until you've run your scanners at least once and written down what *they* report.
The point is to compare their findings with this list, and to ask why anything is missing.

| # | Flaw | Where | Which stage should catch it |
|---|------|-------|-----------------------------|
| 1 | Hardcoded API key | `notesapp/config.py` (`INTERNAL_API_KEY`) | Secrets scan (also try the history angle, see below) |
| 2 | Weak default signing key (`changeme`) | `notesapp/config.py` | Probably nobody. Code review / your own rule |
| 3 | Dependencies with known CVEs | `requirements.txt` (Flask, Werkzeug, requests, gunicorn are old) | SCA. Check what the scanner actually reports |
| 4 | SQL injection | `routes.py` `/search` | SAST, and DAST (active/API scan only) |
| 5 | SSRF | `routes.py` `/fetch` | SAST maybe; DAST unlikely without help |
| 6 | Reflected XSS | `routes.py` `/hello` | SAST, DAST |
| 7 | Weak hash (MD5) | `routes.py` `create_note` | SAST |
| 8 | Flask debug mode on | `wsgi.py` | SAST, and a runtime Docker check |
| 9 | No security headers | the whole app | DAST baseline scan |

## Flaws that are yours to avoid or find

- Nothing here forces `USER root` in Docker. You will decide the user, the base image and the file permissions.
- Secret in git history: commit a fake secret in a `.env`, delete it in the next commit, push, and see
  whether your secrets scan notices. (Hint: `fetch-depth`.)
- Does a scanner that passes mean the app is safe? Write down which flaws above were NOT caught and why.

## Questions to answer with evidence

1. Which flaws were found by which tool, and which were found by none?
2. For each CVE the SCA reports: is the vulnerable code path actually reachable in this app?
3. What threshold fails your build, and what would that threshold have done to this repo?
