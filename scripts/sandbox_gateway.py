import os
import json
import uuid
from datetime import datetime, timezone

CURRENCY = "CAD"

def process_sandbox_payment(bill_id, biller_name, amount):
    """
    Simulates a Payments Canada Real-Time Rail (RTR) API sandbox call 
    using ISO 20022 (pacs.008 Customer Credit Transfer) data structures.
    """
    end_to_end_id = f"RTR-E2E-{uuid.uuid4().hex[:12].upper()}"
    instruction_id = f"RTR-INS-{uuid.uuid4().hex[:12].upper()}"
    execution_time = datetime.now(timezone.utc).isoformat()
    
    amount_str = f"{amount:.2f}"
    
    print(f"[PAYMENTS CANADA RTR SANDBOX] Dispatching ISO 20022 pacs.008 payload...")
    print(f"[PAYMENTS CANADA RTR SANDBOX] Biller: {biller_name} | Amount: {CURRENCY} ${amount_str}")

    # ISO 20022 aligned message structure for Canadian Real-Time Rail simulation
    iso_pacs_008_payload = {
        "document": {
            "FIToFICstmrCdtTrf": {
                "GrpHdr": {
                    "MsgId": instruction_id,
                    "CreDtTm": execution_time,
                    "NbOfTxs": "1",
                    "SttlmInf": {
                        "SttlmMtd": "CLRG"
                    }
                },
                "CdtTrfTxInf": {
                    "PmtId": {
                        "EndToEndId": end_to_end_id
                    },
                    "IntrBkSttlmAmt": {
                        "Ccy": CURRENCY,
                        "Value": amount_str
                    },
                    "Cdtr": {
                        "Nm": biller_name
                    },
                    "RmtInf": {
                        "Ustrd": f"Automated billing execution for bill ID {bill_id}"
                    }
                }
            }
        },
        "sandbox_status": "ACCP", # ISO code for Accepted Customer Profile / Settlement Success
        "clearing_rail": "CANADIAN_RTR_SANDBOX"
    }

    return {
        "status": "SUCCESS",
        "response_code": 200,
        "data": iso_pacs_008_payload
    }

if __name__ == "__main__":
    result = process_sandbox_payment(101, "Hydro Edmonton Utility", 95.40)
    print(json.dumps(result, indent=2))
