import re


def validate_old_indian_car_number(number_plate):
    """
    Validates a traditional Indian car number plate format using regular expressions.
    This version specifically allows for optional spaces but no hyphens and does not
    match the newer Bharat series (BH).

    Args:
        number_plate (str): The number plate string to validate.

    Returns:
        bool: True if the format is valid, False otherwise.
    """
    # Define a regex pattern for the standard Indian number plate.
    # r'': raw string to prevent misinterpretation of backslashes.
    # ^: asserts the start of the string.
    # [A-Z]{2}: matches exactly two uppercase English letters (State code).
    # \s?: matches an optional space.
    # [0-9]{1,2}: matches one or two digits (RTO district code).
    # \s?: matches an optional space.
    # [A-Z]{1,2}: matches one or two uppercase letters (series code).
    # \s?: matches an optional space.
    # [0-9]{4}: matches exactly four digits (the unique vehicle number).
    # $: asserts the end of the string.

    # We use optional spaces `\s?` between each part to be lenient with spacing.
    traditional_pattern = r'^[A-Z]{2}\s?[0-9]{1,2}\s?[A-Z]{1,2}\s?[0-9]{4}$'

    # Normalize the input string to uppercase before checking
    # for a more reliable match.
    return re.match(traditional_pattern, number_plate.upper()) is not None

# --- Examples of usage ---


# Valid plates with spaces
plate_1 = "GJ 03 AY 1097"
# Expected: True
print(f"'{plate_1}' is a valid traditional plate: {validate_old_indian_car_number(plate_1)}")

# Valid plate with no spaces
plate_2 = "GJ03AY1097"
# Expected: True
print(f"'{plate_2}' is a valid traditional plate: {validate_old_indian_car_number(plate_2)}")

# Valid plate with some spaces
plate_3 = "DL 01 AB 9876"
# Expected: True
print(f"'{plate_3}' is a valid traditional plate: {validate_old_indian_car_number(plate_3)}")

# Invalid plate with hyphens
invalid_plate_1 = "MH-05-DL-9023"
# Expected: False
print(f"'{invalid_plate_1}' is a valid traditional plate: {validate_old_indian_car_number(invalid_plate_1)}")

# Invalid plate due to BH series
invalid_plate_2 = "22 BH 4928 A"
# Expected: False
print(f"'{invalid_plate_2}' is a valid traditional plate: {validate_old_indian_car_number(invalid_plate_2)}")

# Invalid plate with extra characters
invalid_plate_3 = "DL 29 KJX 0001"
# Expected: False
print(f"'{invalid_plate_3}' is a valid traditional plate: {validate_old_indian_car_number(invalid_plate_3)}")
