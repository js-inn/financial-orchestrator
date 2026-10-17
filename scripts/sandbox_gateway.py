import os
import json
import uuid
import hashlib
from datetime import datetime, timezone

CURRENCY = "CAD"

def process_sandbox_payment(bill_id, biller_name, amount, force_error=False):
    """
    Simulates an institutional Payments Canada RTR workflow with:
    - Idempotency hashing
    - ISO 20022 pacs.008 (Payment Instruction)
    - ISO 20022 pacs.002 (Asynchronous Settlement Status Report)
    - Error injection testing
    """
    # 1. Generate a strict idempotency key based on bill metadata
    raw_idempotency_string = f"{bill_id}-{biller_name}-{amount:.2f}-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    idempotency_key = hashlib.sha256(raw_idempotency_string.encode('utf-8')).hexdigest()
    
    end_to_end_id = f"RTR-E2E-{uuid.uuid4().hex[:12].upper()}"
    instruction_id = f"RTR-INS-{uuid.uuid4().hex[:12].upper()}"
    execution_time = datetime.now(timezone.utc).isoformat()
    amount_str = f"{amount:.2f}"
    
    print(f"[RTR GATEWAY] Preparing payload for {biller_name} | Amount: CAD ${amount_str}")
    print(f"[RTR GATEWAY] Idempotency Key: {idempotency_key[:16]}...")

    # If force_error is triggered, simulate a network rejection (e.g., ISO code RJCT)
    if force_error:
        print(f"[RTR GATEWAY] [SIMULATION ERROR] Clearing house rejected payment for {biller_name}.")
        return {
            "status": "FAILED",
            "response_code": 422,
            "data": {
                "idempotency_key": idempotency_key,
                "pacs_002_status_report": {
                    "OrgnlGrpInf": {"OrgnlMsgId": instruction_id},
                    "TxSts": "RJCT",
                    "Rsn": {"Prtry": "AC04 - Closed Account / Simulation Rejection"}
                }
            }
        }

    # Standard successful ISO 20022 Payload flow
    iso_pacs_008_payload = {
        "idempotency_key": idempotency_key,
        "document": {
            "FIToFICstmrCdtTrf": {
                "GrpHdr": {
                    "MsgId": instruction_id,
                    "CreDtTm": execution_time,
                    "NbOfTxs": "1",
                    "SttlmInf": {"SttlmMtd": "CLRG"}
                },
                "CdtTrfTxInf": {
                    "PmtId": {"EndToEndId": end_to_end_id},
                    "IntrBkSttlmAmt": {"Ccy": CURRENCY, "Value": amount_str},
                    "Cdtr": {"Nm": biller_name},
                    "RmtInf": {"Ustrd": f"Sole-proprietor automated settlement for bill ID {bill_id}"}
                }
            }
        },
        # Asynchronous status acknowledgment (pacs.002 equivalent)
        "pacs_002_status_report": {
            "TxSts": "ACCP", # Accepted / Settlement Complete
            "ClrSysRef": f"RTR-CLR-{uuid.uuid4().hex[:8].upper()}"
        },
        "clearing_rail": "CANADIAN_RTR_SANDBOX"
    }

    return {
        "status": "SUCCESS",
        "response_code": 200,
        "data": iso_pacs_008_payload
    }

if __name__ == "__main__":
    # Test execution
    res = process_sandbox_payment(999, "Test Vendor", 50.00)
    print(json.dumps(res, indent=2))
