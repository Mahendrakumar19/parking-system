import re


def validate_debit_card_details(card_number, cvv, name, expiry_date):
    """
    Validates Indian debit card details (Visa, Mastercard, RuPay).

    Args:
        card_number (str): The debit card number.
        cvv (str): The CVV number.
        name (str): The cardholder's name.
        expiry_date (str): The expiry date of the card.
    Returns:
        tuple: A tuple containing booleans for the validity of the card number,
               CVV, and name, respectively.
    """
    # Remove all spaces from the card number for validation
    cleaned_card_number = card_number.replace(" ", "")

    # Regex pattern for 16-digit card numbers (Visa, Mastercard, RuPay)
    # Visa starts with 4, Mastercard with 51-55, RuPay with 6.
    card_number_pattern = r'^(?:4[0-9]{15}|5[1-5][0-9]{14}|6(?:011|5[0-9]{2})[0-9]{12})$'

    # Regex pattern for 3-digit CVV (Visa, Mastercard, RuPay)
    cvv_pattern = r'^[0-9]{3}$'

    # Simple regex pattern for a name, allowing alphabets and spaces
    name_pattern = r'^[a-zA-Z\s]+$'

    # Regex pattern for expiry date (Look for YY format in the future)
    expiry_date_pattern = r'^(0[1-9]|1[0-2])\/([0-9]{2})$'
    expiry_match = re.match(expiry_date_pattern, expiry_date)
    expiry_date_valid = False

    if expiry_match:
        month = int(expiry_match.group(1))
        year = int(expiry_match.group(2))
        # Add 2000 to convert YY to YYYY (year 25 = 2025)
        full_year = 2000 + year

        # Validate month is 1-12 and year is not expired
        current_year = 2025
        if 1 <= month <= 12 and full_year >= current_year:
            expiry_date_valid = True
    # Validate each component
    is_card_number_valid = re.match(
        card_number_pattern, cleaned_card_number) is not None
    is_cvv_valid = re.match(cvv_pattern, cvv) is not None
    is_name_valid = re.match(name_pattern, name) is not None
    return is_card_number_valid, is_cvv_valid, is_name_valid, expiry_date_valid


# --- Example of usage ---
# Valid details
card_num_valid = "4111 1111 1111 1111"
cvv_valid = "123"
name_valid = "RAJESH SHARMA"

# Invalid details
card_num_invalid = "9999 9999 9999 9999"  # Invalid card network
cvv_invalid = "1234"  # Invalid CVV length
name_invalid = "Rajesh Sharma 123"  # Invalid characters in name

# Test the validation function
expiry_valid = "12/25"
expiry_invalid = "01/20"

print(f"Details for '{name_valid}' with card number '{card_num_valid}':")
card_ok, cvv_ok, name_ok, expiry_ok = validate_debit_card_details(
    card_num_valid, cvv_valid, name_valid, expiry_valid)
print(f"  Card number valid: {card_ok}")
print(f"  CVV valid: {cvv_ok}")
print(f"  Name valid: {name_ok}")
print(f"  Expiry valid: {expiry_ok}\n")

print(f"Details for invalid expiry '{expiry_invalid}':")
card_ok, cvv_ok, name_ok, expiry_ok = validate_debit_card_details(
    card_num_valid, cvv_valid, name_valid, expiry_invalid)
print(f"  Card number valid: {card_ok}")
print(f"  CVV valid: {cvv_ok}")
print(f"  Name valid: {name_ok}")
print(f"  Expiry valid: {expiry_ok}\n")
