zodiac_signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]


def calculate_d2_position(current_sign, sign_lon_dec_deg):
    # Determine the sign index
    sign_index = zodiac_signs.index(current_sign)
    is_odd_sign = sign_index % 2 == 0  # Odd signs: Aries, Gemini, etc.

    # Assign Hora based on gender
    if sign_lon_dec_deg < 15:
        new_sign = "Leo" if is_odd_sign else "Cancer"  # First 15°
    else:
        new_sign = "Cancer" if is_odd_sign else "Leo"  # Second 15°

    # Degree within the Hora
    new_degree = sign_lon_dec_deg % 15

    return new_sign, new_degree

def calculate_d3_position(current_sign, sign_lon_dec_deg):
    """
    Calculates D-3 position using Yavana Paddhati (based on trines).
    """
    trines = {
        "Aries": ["Aries", "Leo", "Sagittarius"],
        "Taurus": ["Taurus", "Virgo", "Capricorn"],
        "Gemini": ["Gemini", "Libra", "Aquarius"],
        "Cancer": ["Cancer", "Scorpio", "Pisces"],
        "Leo": ["Leo", "Sagittarius", "Aries"],
        "Virgo": ["Virgo", "Capricorn", "Taurus"],
        "Libra": ["Libra", "Aquarius", "Gemini"],
        "Scorpio": ["Scorpio", "Pisces", "Cancer"],
        "Sagittarius": ["Sagittarius", "Aries", "Leo"],
        "Capricorn": ["Capricorn", "Taurus", "Virgo"],
        "Aquarius": ["Aquarius", "Gemini", "Libra"],
        "Pisces": ["Pisces", "Cancer", "Scorpio"]
    }
    part_size = 10  # Each division is 10°
    part_number = int(sign_lon_dec_deg // part_size)
    remainder = sign_lon_dec_deg % part_size

    # Get the corresponding trine
    new_sign = trines[current_sign][part_number]
    return new_sign, remainder

def calculate_d4_position(current_sign, sign_lon_dec_deg):
    """
    Calculates the D-4 position using Yavana Paddhati (based on Kendras).
    """
    part_size = 7.5
    part_number = int(sign_lon_dec_deg // part_size)
    remainder = sign_lon_dec_deg % part_size

    # Determine the new sign based on Kendra logic
    kendra_offsets = [0, 3, 6, 9]
    current_sign_index = zodiac_signs.index(current_sign)
    new_sign_index = (current_sign_index + kendra_offsets[part_number]) % 12
    new_sign = zodiac_signs[new_sign_index]

    return new_sign, remainder

def calculate_d5_position(current_sign, sign_lon_dec_deg):
    """
    Calculates the D-5 (Panchamsha) position using Yavana Paddhati.
    """
    # Define the element groups and their corresponding sign cycles
    element_cycles = {
        "Aries": ["Aries", "Leo", "Sagittarius", "Aries", "Leo"],
        "Leo": ["Aries", "Leo", "Sagittarius", "Aries", "Leo"],
        "Sagittarius": ["Aries", "Leo", "Sagittarius", "Aries", "Leo"],
        "Taurus": ["Taurus", "Virgo", "Capricorn", "Taurus", "Virgo"],
        "Virgo": ["Taurus", "Virgo", "Capricorn", "Taurus", "Virgo"],
        "Capricorn": ["Taurus", "Virgo", "Capricorn", "Taurus", "Virgo"],
        "Gemini": ["Gemini", "Libra", "Aquarius", "Gemini", "Libra"],
        "Libra": ["Gemini", "Libra", "Aquarius", "Gemini", "Libra"],
        "Aquarius": ["Gemini", "Libra", "Aquarius", "Gemini", "Libra"],
        "Cancer": ["Cancer", "Scorpio", "Pisces", "Cancer", "Scorpio"],
        "Scorpio": ["Cancer", "Scorpio", "Pisces", "Cancer", "Scorpio"],
        "Pisces": ["Cancer", "Scorpio", "Pisces", "Cancer", "Scorpio"]
    }

    # Ensure the current sign is valid
    if current_sign not in element_cycles:
        raise ValueError(f"Invalid sign: {current_sign}")

    # Determine the part size and calculate the part number
    part_size = 6  # Each division is 6°
    part_number = int(sign_lon_dec_deg // part_size)
    remainder = sign_lon_dec_deg % part_size

    # Get the new sign based on the part number
    new_sign = element_cycles[current_sign][part_number]

    return new_sign, remainder

def calculate_d7_position(current_sign, sign_lon_dec_deg):
    """
    Calculates the D-7 position based on Saptamsha rules for odd and even signs.
    """
    # Part size for D-7 is 4°17' (4.2833 degrees)
    part_size = 4.2833
    part_number = int(sign_lon_dec_deg // part_size)  # 0 to 6 for 7 parts
    remainder = sign_lon_dec_deg % part_size

    # Define odd and even sign rules
    odd_sign_order = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    even_sign_order = [7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6]

    current_sign_index = zodiac_signs.index(current_sign) + 1  # Zodiac signs are 1-based

    # Determine the new sign
    if current_sign_index % 2 == 1:  # Odd sign logic
        new_sign_index = (current_sign_index - 1 + part_number) % 12
    else:  # Even sign logic
        new_sign_index = (6 + current_sign_index - 1 + part_number) % 12

    new_sign = zodiac_signs[new_sign_index]
    return new_sign, remainder

def calculate_d9_position(current_sign, sign_lon_dec_deg):
    """
    Calculates the D-9 position based on Navamsa rules.
    """
    # Part size for D-9 is 3°20' (3.3333 degrees)
    part_size = 3.3333
    part_number = int(sign_lon_dec_deg // part_size)  # 0 to 8 for 9 parts
    remainder = sign_lon_dec_deg % part_size

    # Define starting sign for each element
    element_start_signs = {
        "Fire": "Aries",
        "Earth": "Capricorn",
        "Air": "Libra",
        "Water": "Cancer"
    }

    # Determine the element of the current sign
    sign_elements = {
        "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
        "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
        "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
        "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water"
    }

    # Get the element and starting sign
    element = sign_elements[current_sign]
    start_sign = element_start_signs[element]

    # Map the part number to the zodiac
    start_index = zodiac_signs.index(start_sign)  # Start index for the element
    new_sign_index = (start_index + part_number) % 12
    new_sign = zodiac_signs[new_sign_index]

    return new_sign, remainder

