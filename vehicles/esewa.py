"""
eSewa ePay v2 integration helpers.

eSewa docs: https://developer.esewa.com.np/pages/Epay

These are eSewa's OFFICIAL PUBLIC SANDBOX/TEST credentials, published in their developer
documentation for testing integrations. They are not secret and are safe to keep in source
control for development. Replace them with your real merchant code and secret key (obtained
after registering as a merchant with eSewa) before going live — see settings via environment
variables ESEWA_MERCHANT_CODE / ESEWA_SECRET_KEY.
"""
import base64
import hashlib
import hmac
import json

from django.conf import settings


def generate_signature(total_amount, transaction_uuid, product_code, secret_key):
    """
    eSewa requires an HMAC-SHA256 signature over a specific comma-joined string of field
    values, matching the order given in signed_field_names.
    """
    message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    hash_bytes = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(hash_bytes).decode('utf-8')


def build_payment_payload(booking, success_url, failure_url):
    """Builds the full set of hidden form fields required by eSewa's ePay v2 payment form."""
    amount = str(booking.payment.amount)
    transaction_uuid = booking.payment.transaction_uuid
    product_code = settings.ESEWA_MERCHANT_CODE

    signature = generate_signature(amount, transaction_uuid, product_code, settings.ESEWA_SECRET_KEY)

    return {
        "amount": amount,
        "tax_amount": "0",
        "total_amount": amount,
        "transaction_uuid": transaction_uuid,
        "product_code": product_code,
        "product_service_charge": "0",
        "product_delivery_charge": "0",
        "success_url": success_url,
        "failure_url": failure_url,
        "signed_field_names": "total_amount,transaction_uuid,product_code",
        "signature": signature,
    }


def decode_esewa_response(encoded_data):
    """eSewa redirects back to success_url with a base64-encoded JSON payload in ?data=..."""
    try:
        decoded_bytes = base64.b64decode(encoded_data)
        return json.loads(decoded_bytes.decode('utf-8'))
    except Exception:
        return None


def verify_response_signature(response_data, secret_key):
    """Recomputes the signature from the decoded response and compares it against eSewa's."""
    if not response_data or 'signature' not in response_data:
        return False

    signed_field_names = response_data.get('signed_field_names', '')
    fields = signed_field_names.split(',')
    message = ",".join(f"{field}={response_data.get(field, '')}" for field in fields)

    expected_signature_bytes = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(expected_signature_bytes).decode('utf-8')

    return hmac.compare_digest(expected_signature, response_data.get('signature', ''))


def check_transaction_status(status_check_url, product_code, total_amount, transaction_uuid, timeout=10):
    """
    Calls eSewa's server-side status check API directly — this is the authoritative source
    of truth and should be checked in addition to (not instead of) the redirect signature,
    since a redirect URL could in theory be replayed or tampered with.
    Returns the parsed JSON response, or None if the request fails.
    """
    import requests
    try:
        response = requests.get(
            status_check_url,
            params={
                "product_code": product_code,
                "total_amount": total_amount,
                "transaction_uuid": transaction_uuid,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None
