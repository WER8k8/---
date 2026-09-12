# P3 B2B Sidecars — LinkedIn + Customs Brief

Dev stack extends P2 (`scripts/start-p3-sidecars-dev.ps1`).

| Service | Port | Env | Compliance |
|---------|------|-----|------------|
| LinkedIn decision-maker | 8095 | `LINKEDIN_DECISION_MAKER_URL` | `restricted` — requires `tenant_consent` + `compliance_acknowledged` |
| Customs buyer brief | API only | M1 public stats | No unverified buyer lists (`buyer_history: null`) |

## Start (development)

```powershell
powershell -File scripts/start-p3-sidecars-dev.ps1
powershell -File scripts/start-dev-admin.ps1 -ForceRestart
```

## Verify

```powershell
cd backend
.\.venv\Scripts\python.exe ..\scripts\verify-linkedin-decision-maker-sidecar.py --smoke
.\.venv\Scripts\python.exe ..\scripts\verify-customs-buyer-brief.py
.\.venv\Scripts\python.exe -m pytest tests/unit/test_p3_sidecars.py -q
```

## API

- `GET /api/v1/foreign-trade/integrations/sidecars/status` — includes `linkedin_decision_maker`
- `POST /api/v1/foreign-trade/integrations/linkedin/decision-makers` — body: `company`, `purpose`, `tenant_consent`, `compliance_acknowledged`
- `GET /api/v1/foreign-trade/trade-intel/customs-buyer-brief?product=&hs_code=&country_code=`

## Honesty gates

- LinkedIn contacts **must** include `evidence_url`; dev stub exposes `mode=mock` / `probe_mode=stub`
- Customs brief returns **playbook + public stats only**; historical buyers require future CustomsDataSpider sidecar
