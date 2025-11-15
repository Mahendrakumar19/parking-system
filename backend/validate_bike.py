import re


def validate_indian_plate(plate_number):
    """
    Validates an Indian vehicle number plate using a regular expression.

    Args:
        plate_number (str): The vehicle number plate string to validate.

    Returns:
        bool: True if the plate is valid, False otherwise.
    """
    # Regex pattern for a standard Indian number plate (e.g., MH 03 AA 4567)
    # ^[A-Z]{2}: Start of string, followed by 2 uppercase letters (state code)
    # \s?: Optional space
    # [0-9]{1,2}: 1 to 2 digits (RTO district code)
    # \s?: Optional space
    # [A-Z]{1,3}: 1 to 3 optional uppercase letters (series code)
    # \s?: Optional space
    # [0-9]{4}$: 4 digits (unique number), followed by end of string
    pattern = r'^[A-Z]{2}\s?[0-9]{1,2}\s?[A-Z]{1,3}\s?[0-9]{4}$'

    if re.match(pattern, plate_number):
        return True
    else:
        return False


# Example usage:
# plate1 = "MH03AA4567"
# plate2 = "GJ 01 AY 1097"
# plate3 = "UP 50 BY 1998"
# plate4 = "invalid_plate"

# print(f"'{plate1}' is valid: {validate_indian_plate(plate1)}")
# print(f"'{plate2}' is valid: {validate_indian_plate(plate2)}")
# print(f"'{plate3}' is valid: {validate_indian_plate(plate3)}")
# print(f"'{plate4}' is valid: {validate_indian_plate(plate4)}")
