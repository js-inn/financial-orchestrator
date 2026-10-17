import os
import json
import uuid
from datetime import datetime, timezone

# Sandbox environment configuration
SANDBOX_MODE = os.getenv("SANDBOX_MODE", "true")
CURRENCY = "CAD"

def process_sandbox_payment(bill_id, biller_name, amount):
    """
    Simulates a secure external API call to a Canadian payment sandbox 
    (such as a Stripe Testmode or ISO 20022 clearing gateway).
    """
    transaction_reference = f"CA-SANDBOX-{uuid.uuid4().hex[:10].upper()}"
    execution_time = datetime.now(timezone.utc).isoformat()
    
    # Convert CAD amount to cents for institutional accuracy
    amount_in_cents = int(round(amount * 100))
    
    print(f"[SANDBOX GATEWAY] Connecting to secure payment clearing endpoint...")
    print(f"[SANDBOX GATEWAY] Processing {CURRENCY} ${amount:.2f} for biller: {biller_name}")

    # Constructing a standard institutional payment response payload
    response_payload = {
        "transaction_id": transaction_reference,
        "status": "APPROVED",
        "currency": CURRENCY,
        "amount_cents": amount_in_cents,
        "biller": biller_name,
        "clearing_rail": "CANADIAN_TEST_EFT_RAIL",
        "timestamp": execution_time,
        "secure_token": f"tok_test_canada_{uuid.uuid4().hex[:6]}"
    }

    return {
        "status": "SUCCESS",
        "response_code": 200,
        "data": response_payload
    }

if __name__ == "__main__":
    # Quick standalone test of the sandbox gateway
    result = process_sandbox_payment(999, "Test Utility Provider Corp", 125.50)
    print(json.dumps(result, indent=2))
