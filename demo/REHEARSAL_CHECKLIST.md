# GigGuard — Pre-Demo Rehearsal Checklist
## Run this top to bottom before judges arrive

---

## 1. Reset Environment
- [ ] Run: python demo/seed_demo.py
- [ ] Confirm output: "Seeding complete" printed
- [ ] Confirm: curl http://localhost:8000/api/dashboard/GG-2026-001 returns JSON

## 2. Verify PDF
- [ ] Confirm output/GG-2026-001.pdf exists
- [ ] Open it — check 3 pages load, no broken characters
- [ ] Amount shows as Rs. 1,840 (not broken symbol)

## 3. Start Server
- [ ] Run: uvicorn main:app --reload
- [ ] Confirm: http://localhost:8000/health returns {"status":"ok"}

## 4. Test Dashboard
- [ ] Open: http://localhost:8000/dashboard/index.html?case=GG-2026-001
- [ ] Case Overview card shows: GG-2026-001, Swiggy, OPEN
- [ ] Worker phone shows: +91 XXXX XX 4821 (masked)
- [ ] Amount shows: Rs. 1,840
- [ ] Timeline shows: Case Filed on 7 June 2026
- [ ] Click View Grievance Letter — PDF opens in new tab

## 5. Test WhatsApp Flow
- [ ] Send "Hi" to sandbox number — greeting arrives
- [ ] Send Swiggy screenshot — OCR confirmation message arrives
- [ ] Reply YES — pipeline triggers
- [ ] Confirm no errors in uvicorn terminal

## 6. Failure Points and Fallbacks
- WhatsApp sandbox times out → use screen recording
- PDF button 404 → open output/GG-2026-001.pdf directly
- Dashboard blank → curl the API, show JSON to judges
- uvicorn crashes → restart with uvicorn main:app --reload
- DB empty → run python demo/seed
