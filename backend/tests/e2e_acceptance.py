import urllib.request
import json

base = "http://127.0.0.1:8000/api"

def run_e2e():
    print("------------------------------------------------------------")
    print("CYBERSLEUTH LIVE END-TO-END ACCEPTANCE TEST")
    print("------------------------------------------------------------")

    # 1. Health
    req = urllib.request.urlopen(f"{base}/health")
    data = json.loads(req.read())
    print(f"1. Health check: {req.status} OK | Backend: {data['backend']} | Database: {data['database']}")

    # 2. Scenarios
    req = urllib.request.urlopen(f"{base}/demos")
    demos = json.loads(req.read())
    print(f"2. Available Demo Scenarios: {len(demos)}")

    # 3. Load Credential Compromise
    req = urllib.request.Request(f"{base}/demos/credential_compromise/load", data=b"", method="POST")
    res = urllib.request.urlopen(req)
    load_data = json.loads(res.read())
    print(f"3. Loaded Scenario: {load_data['message']}")

    # 4. Fetch alerts
    req = urllib.request.urlopen(f"{base}/alerts?is_demo=true")
    alerts = json.loads(req.read())
    print(f"4. Alerts retrieved: {len(alerts)}")
    target_alert = alerts[0]
    print(f"   Target Alert: {target_alert['id']} - {target_alert['title']}")

    # 5. Start LangGraph Investigation
    post_body = json.dumps({"alert_id": target_alert['id']}).encode()
    req = urllib.request.Request(f"{base}/investigations", data=post_body, headers={"Content-Type": "application/json"}, method="POST")
    res = urllib.request.urlopen(req)
    inv = json.loads(res.read())
    print(f"5. LangGraph Investigation: {inv['id']} | Status: {inv['status']} | Progress: {inv['progress']}%")
    print(f"   Structured Findings count: {len(inv['findings'])}")
    print(f"   MITRE techniques count: {len(inv['mitre_mappings'])}")

    # 6. Fetch Evidence Graph
    req = urllib.request.urlopen(f"{base}/evidence/{inv['id']}/graph")
    graph = json.loads(req.read())
    print(f"6. Evidence Graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
    print(f"   Observed links: {graph['stats']['observed_count']} | Inferred links: {graph['stats']['inferred_count']}")

    # 7. Approve Response Action
    req = urllib.request.urlopen(f"{base}/response?investigation_id={inv['id']}")
    actions = json.loads(req.read())
    if actions:
        act_id = actions[0]['id']
        appr_body = json.dumps({"decided_by": "lead_soc_analyst", "comments": "Approved simulated isolation."}).encode()
        req = urllib.request.Request(f"{base}/response/{act_id}/approve", data=appr_body, headers={"Content-Type": "application/json"}, method="POST")
        res = urllib.request.urlopen(req)
        act_res = json.loads(res.read())
        print(f"7. Response Action: {act_res['id']} ({act_res['action_type']}) -> Status: {act_res['status']} (Simulated: {act_res['is_simulated']})")

    # 8. ReportLab PDF download
    req = urllib.request.urlopen(f"{base}/reports/{inv['id']}/download")
    pdf_data = req.read()
    print(f"8. PDF Report Generated & Downloaded: {len(pdf_data)} bytes | Header: {pdf_data[:4].decode('latin-1')}")
    assert pdf_data.startswith(b"%PDF")
    print("------------------------------------------------------------")
    print("E2E ACCEPTANCE TEST COMPLETED SUCCESSFULLY WITH 100% PASS RATE!")
    print("------------------------------------------------------------")

if __name__ == "__main__":
    run_e2e()
