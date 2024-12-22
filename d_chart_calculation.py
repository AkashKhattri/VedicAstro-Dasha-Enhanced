from typing import List, Tuple

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

def calculate_d10_position(current_sign, sign_lon_dec_deg):
    """
    Calculates the D-10 position based on the degree range within a sign
    directly mapped to the corresponding D-10 sign.
    """
    # Dasamsa part size and corresponding D-10 signs mapping
    d10_signs_mapping = [
        [1, 10, 3, 12, 5, 2, 7, 4, 9, 6, 11, 8],  # Part 1 (0°-3°)
        [2, 11, 4, 1, 6, 3, 8, 5, 10, 7, 12, 9],  # Part 2 (3°-6°)
        [3, 12, 5, 2, 7, 4, 9, 6, 11, 8, 1, 10],  # Part 3 (6°-9°)
        [4, 1, 6, 3, 8, 5, 10, 7, 12, 9, 2, 11],  # Part 4 (9°-12°)
        [5, 2, 7, 4, 9, 6, 11, 8, 1, 10, 3, 12],  # Part 5 (12°-15°)
        [6, 3, 8, 5, 10, 7, 12, 9, 2, 11, 4, 1],  # Part 6 (15°-18°)
        [7, 4, 9, 6, 11, 8, 1, 10, 3, 12, 5, 2],  # Part 7 (18°-21°)
        [8, 5, 10, 7, 12, 9, 2, 11, 4, 1, 6, 3],  # Part 8 (21°-24°)
        [9, 6, 11, 8, 1, 10, 3, 12, 5, 2, 7, 4],  # Part 9 (24°-27°)
        [10, 7, 12, 9, 2, 11, 4, 1, 6, 3, 8, 5],  # Part 10 (27°-30°)
    ]

    # Calculate the part number based on degrees within the sign
    part_size = 3.0
    part_number = int(sign_lon_dec_deg // part_size)  # 0 to 9 for 10 parts

    # Determine the D-10 sign using the table
    current_sign_index = zodiac_signs.index(current_sign)  # Get 0-based index for current sign
    new_sign_index = d10_signs_mapping[part_number][current_sign_index] - 1  # Convert 1-based to 0-based
    new_sign = zodiac_signs[new_sign_index]

    # Calculate the remaining degrees within the part
    remainder = sign_lon_dec_deg % part_size

    return new_sign, remainder

def calculate_d12_position(current_sign, sign_lon_dec_deg):
    """
    Calculates the D-12 position based on the rules for Dwadasamsa.
    Parameters:
        current_sign: The zodiac sign name
        sign_lon_dec_deg: Longitude within the sign (0-30 degrees)
    Returns:
        Tuple of (new_sign, remainder_degrees)
    """
    # Verify input range
    if not 0 <= sign_lon_dec_deg < 30:
        raise ValueError("Sign longitude must be between 0 and 30 degrees")

    part_size = 2.5
    part_number = int(sign_lon_dec_deg // part_size)
    remainder = sign_lon_dec_deg % part_size

    # Calculate D-12 position following sign rulership pattern
    # In D-12, each sign is divided into 12 parts ruled by signs starting
    # from the sign itself
    start_index = zodiac_signs.index(current_sign)
    new_sign_index = (start_index + part_number) % 12
    new_sign = zodiac_signs[new_sign_index]

    return new_sign, remainder

def calculate_d16_position(current_sign, sign_lon_dec_deg):
    """
    Calculates the D-16 position using the raw mapping data.
    """
    d16_mapping = [
        [1, 5, 9, 1, 5, 9, 1, 5, 9, 1, 5, 9],
        [2, 6, 10, 2, 6, 10, 2, 6, 10, 2, 6, 10],
        [3, 7, 11, 3, 7, 11, 3, 7, 11, 3, 7, 11],
        [4, 8, 12, 4, 8, 12, 4, 8, 12, 4, 8, 12],
        [5, 9, 1, 5, 9, 1, 5, 9, 1, 5, 9, 1],
        [6, 10, 2, 6, 10, 2, 6, 10, 2, 6, 10, 2],
        [7, 11, 3, 7, 11, 3, 7, 11, 3, 7, 11, 3],
        [8, 12, 4, 8, 12, 4, 8, 12, 4, 8, 12, 4],
        [9, 1, 5, 9, 1, 5, 9, 1, 5, 9, 1, 5],
        [10, 2, 6, 10, 2, 6, 10, 2, 6, 10, 2, 6],
        [11, 3, 7, 11, 3, 7, 11, 3, 7, 11, 3, 7],
        [12, 4, 8, 12, 4, 8, 12, 4, 8, 12, 4, 8],
        [1, 5, 9, 1, 5, 9, 1, 5, 9, 1, 5, 9],
        [2, 6, 10, 2, 6, 10, 2, 6, 10, 2, 6, 10],
        [3, 7, 11, 3, 7, 11, 3, 7, 11, 3, 7, 11],
        [4, 8, 12, 4, 8, 12, 4, 8, 12, 4, 8, 12]
    ]

    # Find the index of the current sign
    current_sign_index = zodiac_signs.index(current_sign)

    # Determine the row in the D-16 mapping table
    part_size = 1.875
    part_number = int(sign_lon_dec_deg // part_size)  # 0 to 15 for 16 parts

    # Get the mapped sign index from the table
    new_sign_index = d16_mapping[part_number][current_sign_index] - 1  # Convert 1-based to 0-based index
    new_sign = zodiac_signs[new_sign_index]

    # Calculate the degree within the new part
    remainder = sign_lon_dec_deg % part_size

    return new_sign, remainder

def calculate_d20_position(sign_type, sign_lon_dec_deg, d20_mapping):
    """
    Calculates the D-20 position directly using the mapping table.
    """
    # Each part is 1°30' or 1.5° in D-20
    part_size = 1.5
    part_number = int(sign_lon_dec_deg // part_size)  # Get the part number (0 to 19)
    remainder = sign_lon_dec_deg % part_size

    # Look up the new sign from the mapping
    new_sign = d20_mapping[sign_type][part_number % 12]  # Loop through 12 signs

    return new_sign, remainder

def calculate_d24_position(current_sign, sign_lon_dec_deg):
    """
    Calculates the D-24 position based on the provided table for odd and even signs.

    Parameters:
        current_sign (str): The current zodiac sign.
        sign_lon_dec_deg (float): The longitude in the sign in decimal degrees (0° to 30°).

    Returns:
        new_sign (str): The calculated sign for the D-24 chart.
        remainder (float): The leftover degrees within the part.
    """
    # Normalize degrees to 0–30° range
    sign_lon_dec_deg = sign_lon_dec_deg % 30

    # D-24 chart has 24 parts, each part is 1°15' (1.25°)
    part_size = 1.25
    part_number = int(sign_lon_dec_deg // part_size)  # Determine the part (0 to 23)
    remainder = sign_lon_dec_deg % part_size

    # D-24 table mapping
    d24_mapping = [
        {"Odd": "Leo", "Even": "Cancer"},
        {"Odd": "Virgo", "Even": "Leo"},
        {"Odd": "Libra", "Even": "Virgo"},
        {"Odd": "Scorpio", "Even": "Libra"},
        {"Odd": "Sagittarius", "Even": "Scorpio"},
        {"Odd": "Capricorn", "Even": "Sagittarius"},
        {"Odd": "Aquarius", "Even": "Capricorn"},
        {"Odd": "Pisces", "Even": "Aquarius"},
        {"Odd": "Aries", "Even": "Pisces"},
        {"Odd": "Taurus", "Even": "Aries"},
        {"Odd": "Gemini", "Even": "Taurus"},
        {"Odd": "Cancer", "Even": "Gemini"},
        {"Odd": "Leo", "Even": "Cancer"},
        {"Odd": "Virgo", "Even": "Leo"},
        {"Odd": "Libra", "Even": "Virgo"},
        {"Odd": "Scorpio", "Even": "Libra"},
        {"Odd": "Sagittarius", "Even": "Scorpio"},
        {"Odd": "Capricorn", "Even": "Sagittarius"},
        {"Odd": "Aquarius", "Even": "Capricorn"},
        {"Odd": "Pisces", "Even": "Aquarius"},
        {"Odd": "Aries", "Even": "Pisces"},
        {"Odd": "Taurus", "Even": "Aries"},
        {"Odd": "Gemini", "Even": "Taurus"},
        {"Odd": "Cancer", "Even": "Gemini"},
    ]

    # Determine if the current sign is odd or even
    zodiac_signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    current_sign_index = zodiac_signs.index(current_sign) + 1  # Zodiac signs are 1-based
    is_odd = current_sign_index % 2 == 1

    # Fetch the new sign based on the mapping
    mapping = d24_mapping[part_number]
    new_sign = mapping["Odd"] if is_odd else mapping["Even"]

    return new_sign, remainder

def calculate_d27_position(current_sign, sign_lon_dec_deg):
    """
    Calculates the D-27 position based on the provided table for Fiery, Earthy, Airy, and Watery signs.

    Parameters:
        current_sign (str): The current zodiac sign.
        sign_lon_dec_deg (float): The longitude in the sign in decimal degrees (0° to 30°).

    Returns:
        new_sign (str): The calculated sign for the D-27 chart.
        remainder (float): The leftover degrees within the part.
    """
    # Normalize degrees to 0–30° range
    sign_lon_dec_deg = sign_lon_dec_deg % 30

    # D-27 chart has 27 parts, each part is 1°6'40" (1.1111°)
    part_size = 1 + (6 / 60) + (40 / 3600)  # Convert 1°6'40" to decimal degrees
    part_number = int(sign_lon_dec_deg // part_size)  # Determine the part (0 to 26)
    remainder = sign_lon_dec_deg % part_size

    # D-27 table mapping
    d27_mapping = [
        {"Fiery": "Aries", "Earthy": "Cancer", "Airy": "Libra", "Watery": "Capricorn"},
        {"Fiery": "Taurus", "Earthy": "Leo", "Airy": "Scorpio", "Watery": "Aquarius"},
        {"Fiery": "Gemini", "Earthy": "Virgo", "Airy": "Sagittarius", "Watery": "Pisces"},
        {"Fiery": "Cancer", "Earthy": "Libra", "Airy": "Capricorn", "Watery": "Aries"},
        {"Fiery": "Leo", "Earthy": "Scorpio", "Airy": "Aquarius", "Watery": "Taurus"},
        {"Fiery": "Virgo", "Earthy": "Sagittarius", "Airy": "Pisces", "Watery": "Gemini"},
        {"Fiery": "Libra", "Earthy": "Capricorn", "Airy": "Aries", "Watery": "Cancer"},
        {"Fiery": "Scorpio", "Earthy": "Aquarius", "Airy": "Taurus", "Watery": "Leo"},
        {"Fiery": "Sagittarius", "Earthy": "Pisces", "Airy": "Gemini", "Watery": "Virgo"},
        {"Fiery": "Capricorn", "Earthy": "Aries", "Airy": "Cancer", "Watery": "Libra"},
        {"Fiery": "Aquarius", "Earthy": "Taurus", "Airy": "Leo", "Watery": "Scorpio"},
        {"Fiery": "Pisces", "Earthy": "Gemini", "Airy": "Virgo", "Watery": "Sagittarius"},
    ]

    # Determine if the current sign is Fiery, Earthy, Airy, or Watery
    sign_type_mapping = {
        "Aries": "Fiery", "Leo": "Fiery", "Sagittarius": "Fiery",
        "Taurus": "Earthy", "Virgo": "Earthy", "Capricorn": "Earthy",
        "Gemini": "Airy", "Libra": "Airy", "Aquarius": "Airy",
        "Cancer": "Watery", "Scorpio": "Watery", "Pisces": "Watery"
    }
    current_sign_type = sign_type_mapping[current_sign]

    # Fetch the new sign based on the mapping
    mapping = d27_mapping[part_number % len(d27_mapping)]  # Ensure part_number wraps
    new_sign = mapping[current_sign_type]

    return new_sign, remainder

def calculate_d30_position(current_sign: str, sign_lon_dec_deg: float) -> Tuple[str, float]:
    """
    Calculates the D-30 position based on the tabulated rules.

    For Odd Signs:
    - 0-5° = Mars (1)
    - 5°-10° = Saturn (11)
    - 10°-18° = Jupiter (9)
    - 18°-25° = Mercury (3)
    - 25°-30° = Venus (7)

    For Even Signs:
    - 0-5° = Venus (2)
    - 5°-10° = Mercury (6)
    - 10°-18° = Jupiter (12)
    - 18°-25° = Saturn (10)
    - 25°-30° = Mars (8)
    """
    # Define degree ranges and corresponding lords
    odd_ranges = [
        (0, 5),     # Mars (1)
        (5, 10),    # Saturn (11)
        (10, 18),   # Jupiter (9)
        (18, 25),   # Mercury (3)
        (25, 30)    # Venus (7)
    ]

    even_ranges = [
        (0, 5),     # Venus (2)
        (5, 10),    # Mercury (6)
        (10, 18),   # Jupiter (12)
        (18, 25),   # Saturn (10)
        (25, 30)    # Mars (8)
    ]

    # Define lords and their corresponding signs
    odd_lords = {
        'Mars': 1,
        'Saturn': 11,
        'Jupiter': 9,
        'Mercury': 3,
        'Venus': 7
    }

    even_lords = {
        'Venus': 2,
        'Mercury': 6,
        'Jupiter': 12,
        'Saturn': 10,
        'Mars': 8
    }

    # Determine if current sign is odd or even
    current_sign_index = zodiac_signs.index(current_sign)
    is_odd_sign = (current_sign_index + 1) % 2 == 1

    # Select appropriate ranges and lords
    ranges = odd_ranges if is_odd_sign else even_ranges
    lords = odd_lords if is_odd_sign else even_lords

    # Find which division the degree falls into
    for i, (start, end) in enumerate(ranges):
        if start <= sign_lon_dec_deg < end:
            # Get the lord for this range
            lord = list(lords.keys())[i]
            house_number = lords[lord]
            # Get the corresponding sign for this house number
            new_sign = zodiac_signs[house_number - 1]
            # Calculate the new degree within the division
            division_size = end - start
            new_degree = ((sign_lon_dec_deg - start) / division_size) * 30
            return new_sign, new_degree

    # Handle edge case for exactly 30°
    if sign_lon_dec_deg == 30:
        lord = list(lords.keys())[-1]
        house_number = lords[lord]
        new_sign = zodiac_signs[house_number - 1]
        return new_sign, 30

    raise ValueError(f"Invalid degree value: {sign_lon_dec_deg}")

def calculate_d40_position(current_sign: str, sign_lon_dec_deg: float) -> Tuple[str, float]:
    """
    Calculates the D-40 position based on the table mapping.
    Each section covers specific degree ranges with no gaps.
    """
    # Define the degree ranges with complete coverage from 0° to 30°
    d40_mapping = [
        {
            "ranges": [(0, 0.75), (9.75, 10.5), (18.75, 19.5), (27.75, 28.5)],  # 0°-45'/9°-45'/18°-45'/27°-45'
            "deity": "Vishnu",
            "odd_sign": "Aries",
            "even_sign": "Libra"
        },
        {
            "ranges": [(1.5, 1.75), (10.5, 10.75), (19.5, 19.75), (28.5, 28.75)],  # 1°-30'/10°-30'/19°-30'/28°-30'
            "deity": "Moon",
            "odd_sign": "Taurus",
            "even_sign": "Scorpio"
        },
        {
            "ranges": [(2.25, 2.5), (11.25, 11.5), (20.25, 20.5), (29.25, 29.5)],  # 2°-15'/11°-15'/20°-15'/29°-15'
            "deity": "Marich",
            "odd_sign": "Gemini",
            "even_sign": "Sagittarius"
        },
        {
            "ranges": [(3, 3.25), (12, 12.25), (21, 21.25), (30, 30.25)],  # 3°/12°/21°/30°
            "deity": "Twastha",
            "odd_sign": "Cancer",
            "even_sign": "Capricorn"
        },
        {
            "ranges": [(3.75, 4), (12.75, 13), (21.75, 22)],  # 3°-45'/12°-45'/21°-45'
            "deity": "Dhata",
            "odd_sign": "Leo",
            "even_sign": "Aquarius"
        },
        {
            "ranges": [(4.5, 4.75), (13.5, 13.75), (22.5, 22.75)],  # 4°-30'/13°-30'/22°-30'
            "deity": "Shiva",
            "odd_sign": "Virgo",
            "even_sign": "Pisces"
        },
        {
            "ranges": [(4.25, 4.5), (14.25, 14.5), (23.25, 23.5)],  # 4°-15'/14°-15'/23°-15'
            "deity": "Sun",
            "odd_sign": "Libra",
            "even_sign": "Aries"
        },
        {
            "ranges": [(6, 6.25), (15, 15.25), (24, 24.25)],  # 6°/15°/24°
            "deity": "Yama",
            "odd_sign": "Scorpio",
            "even_sign": "Taurus"
        },
        {
            "ranges": [(6.75, 7), (15.75, 16), (24.75, 25)],  # 6°-45'/15°-45'/24°-45'
            "deity": "Yaksh",
            "odd_sign": "Sagittarius",
            "even_sign": "Gemini"
        },
        {
            "ranges": [(7.5, 7.75), (16.5, 16.75), (25.5, 25.75)],  # 7°-30'/16°-30'/25°-30'
            "deity": "Gandharva",
            "odd_sign": "Capricorn",
            "even_sign": "Cancer"
        },
        {
            "ranges": [(8.25, 8.5), (17.25, 17.5), (26.25, 26.5)],  # 8°-15'/17°-15'/26°-15'
            "deity": "Kaal",
            "odd_sign": "Aquarius",
            "even_sign": "Leo"
        },
        {
            "ranges": [(9, 9.25), (18, 18.25), (27, 27.25)],  # 9°/18°/27°
            "deity": "Varun",
            "odd_sign": "Pisces",
            "even_sign": "Virgo"
        }
    ]
    # Determine if current sign is odd or even
    current_sign_index = zodiac_signs.index(current_sign)
    is_odd_sign = (current_sign_index + 1) % 2 == 1

    # Handle edge case for 30 degrees
    if sign_lon_dec_deg == 30:
        return ("Gemini" if is_odd_sign else "Sagittarius"), 30

    # Find the matching range and get corresponding sign
    for mapping in d40_mapping:
        for start, end in mapping["ranges"]:
            if start <= sign_lon_dec_deg < end:
                new_sign = mapping["odd_sign"] if is_odd_sign else mapping["even_sign"]
                # Calculate the new degree within the range
                range_size = end - start
                position_in_range = (sign_lon_dec_deg - start) / range_size
                new_degree = position_in_range * 30
                return new_sign, new_degree

    # If we get here, something is wrong with the degree value
    raise ValueError(f"Degree {sign_lon_dec_deg} not found in any range. Must be between 0 and 30.")
