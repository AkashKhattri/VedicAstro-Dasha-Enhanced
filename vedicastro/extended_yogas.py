"""
This module extends the existing yoga implementations in the vedicastro package.
It adds additional important yogas from Vedic astrology that were not previously implemented.
"""

def check_additional_benefic_yogas(planet_positions, houses_data):
    """
    Check for additional important benefic yogas not covered in the main module.

    Args:
        planet_positions: Dictionary mapping planet names to their positional data
        houses_data: Dictionary mapping house numbers to house data

    Returns:
        List of dictionaries containing yoga names and descriptions
    """
    additional_yogas = []

    # Get lords of key houses
    house_lords = {}
    for house_num in range(1, 13):
        if house_num in houses_data:
            house_lords[house_num] = houses_data[house_num]["RasiLord"]

    # Sign lords mapping
    sign_lords = {
        "Aries": "Mars",
        "Taurus": "Venus",
        "Gemini": "Mercury",
        "Cancer": "Moon",
        "Leo": "Sun",
        "Virgo": "Mercury",
        "Libra": "Venus",
        "Scorpio": "Mars",
        "Sagittarius": "Jupiter",
        "Capricorn": "Saturn",
        "Aquarius": "Saturn",
        "Pisces": "Jupiter"
    }

    # Benefic planets
    benefics = ["Jupiter", "Venus", "Mercury", "Moon"]

    # --- BENEFIC YOGAS ---

    # Check for Adhi Yoga - benefics in 6th, 7th, and 8th from Moon
    if "Moon" in planet_positions:
        moon_house = planet_positions["Moon"]["HouseNr"]
        sixth_from_moon = (moon_house + 5) % 12 or 12
        seventh_from_moon = (moon_house + 6) % 12 or 12
        eighth_from_moon = (moon_house + 7) % 12 or 12

        benefic_count = 0
        for benefic in benefics:
            if benefic in planet_positions and benefic != "Moon":
                planet_house = planet_positions[benefic]["HouseNr"]
                if planet_house in [sixth_from_moon, seventh_from_moon, eighth_from_moon]:
                    benefic_count += 1

        if benefic_count >= 2:
            additional_yogas.append({
                "name": "Adhi Yoga",
                "description": f"Benefics in 6th, 7th, and/or 8th houses from Moon, conferring leadership, governmental power, and authority."
            })

    # Check for Shankha Yoga - specific planet positions
    # One implementation: Lords of 5th and 6th conjunct in a kendra
    if 5 in house_lords and 6 in house_lords:
        fifth_lord = house_lords[5]
        sixth_lord = house_lords[6]

        if (fifth_lord in planet_positions and
            sixth_lord in planet_positions and
            fifth_lord != sixth_lord):

            fifth_lord_house = planet_positions[fifth_lord]["HouseNr"]
            sixth_lord_house = planet_positions[sixth_lord]["HouseNr"]

            if fifth_lord_house == sixth_lord_house and fifth_lord_house in [1, 4, 7, 10]:
                additional_yogas.append({
                    "name": "Shankha Yoga",
                    "description": "Lords of 5th and 6th houses conjunct in a kendra (angular house), conferring wisdom, diplomacy, and spiritual inclination."
                })

    # Alternative Shankha Yoga - 5th and 6th lords in mutual kendras
    if 5 in house_lords and 6 in house_lords:
        fifth_lord = house_lords[5]
        sixth_lord = house_lords[6]

        if fifth_lord in planet_positions and sixth_lord in planet_positions:
            # Check if they are opposite (7th from each other)
            fifth_lord_house = planet_positions[fifth_lord]["HouseNr"]
            sixth_lord_house = planet_positions[sixth_lord]["HouseNr"]

            if abs(fifth_lord_house - sixth_lord_house) == 6:  # 7 houses apart (opposite)
                additional_yogas.append({
                    "name": "Shankha Yoga",
                    "description": "Lords of 5th and 6th houses in opposition, conferring longevity, morality, and ethical conduct."
                })

    # Check for Maha Bhagya Yoga - Jupiter in Lagna with Moon in 7th or 9th
    if ("Jupiter" in planet_positions and
        "Moon" in planet_positions and
        planet_positions["Jupiter"]["HouseNr"] == 1 and
        planet_positions["Moon"]["HouseNr"] in [7, 9]):

        additional_yogas.append({
            "name": "Maha Bhagya Yoga",
            "description": "Jupiter in Lagna with Moon in 7th or 9th house, conferring extraordinary fortune and success."
        })

    # Check for Kahala Yoga - Saturn and Venus exchange or conjunct in a kendra
    if "Saturn" in planet_positions and "Venus" in planet_positions:
        saturn_house = planet_positions["Saturn"]["HouseNr"]
        venus_house = planet_positions["Venus"]["HouseNr"]
        saturn_sign = planet_positions["Saturn"]["Rasi"]
        venus_sign = planet_positions["Venus"]["Rasi"]

        # Check for conjunction in kendra
        if saturn_house == venus_house and saturn_house in [1, 4, 7, 10]:
            additional_yogas.append({
                "name": "Kahala Yoga",
                "description": "Saturn and Venus conjunct in a kendra (angular house), conferring boldness, authority, and success."
            })

        # Check for exchange
        elif (sign_lords.get(saturn_sign) == "Venus" and
              sign_lords.get(venus_sign) == "Saturn"):

            additional_yogas.append({
                "name": "Kahala Yoga",
                "description": "Saturn and Venus in mutual exchange, conferring boldness, authority, and success."
            })

    # Check for Jnana Yoga - Jupiter or Mercury in 1st, 4th, 5th or 9th house
    for planet in ["Jupiter", "Mercury"]:
        if planet in planet_positions:
            planet_house = planet_positions[planet]["HouseNr"]

            if planet_house in [1, 4, 5, 9]:
                additional_yogas.append({
                    "name": "Jnana Yoga",
                    "description": f"{planet} in house {planet_house}, conferring wisdom, spiritual knowledge, and intellectual abilities."
                })

    return additional_yogas

def check_intellectual_yogas(planet_positions, houses_data):
    """
    Check for yogas specifically related to intelligence, education, and wisdom.

    Args:
        planet_positions: Dictionary mapping planet names to their positional data
        houses_data: Dictionary mapping house numbers to house data

    Returns:
        List of dictionaries containing yoga names and descriptions
    """
    intellectual_yogas = []

    # Get lords of key houses
    house_lords = {}
    for house_num in range(1, 13):
        if house_num in houses_data:
            house_lords[house_num] = houses_data[house_num]["RasiLord"]

    # Check for Saraswati Yoga - Jupiter, Venus and Mercury in angles/trines
    quadrants_and_trines = [1, 4, 5, 7, 9, 10]  # Kendras and Trikonas

    if ("Jupiter" in planet_positions and
        "Venus" in planet_positions and
        "Mercury" in planet_positions):

        jupiter_house = planet_positions["Jupiter"]["HouseNr"]
        venus_house = planet_positions["Venus"]["HouseNr"]
        mercury_house = planet_positions["Mercury"]["HouseNr"]

        if (jupiter_house in quadrants_and_trines and
            venus_house in quadrants_and_trines and
            mercury_house in quadrants_and_trines):

            intellectual_yogas.append({
                "name": "Saraswati Yoga",
                "description": "Jupiter, Venus and Mercury in angles/trines, conferring wisdom, intelligence, artistic abilities, and education."
            })

    # Check for Budha-Aditya Yoga - Sun and Mercury in same sign
    if "Sun" in planet_positions and "Mercury" in planet_positions:
        sun_sign = planet_positions["Sun"]["Rasi"]
        mercury_sign = planet_positions["Mercury"]["Rasi"]

        if sun_sign == mercury_sign:
            # Check if Mercury is not too close to Sun (not combust)
            # This would require exact degrees, so we're simplifying
            intellectual_yogas.append({
                "name": "Budha-Aditya Yoga",
                "description": "Sun and Mercury in same sign, conferring intelligence, communication skills, and administrative abilities."
            })

    # Check for Vidya Yoga - Strong 2nd, 4th, 5th lords
    education_houses = [2, 4, 5]
    strong_education_lords = 0

    for house in education_houses:
        if house in house_lords:
            lord = house_lords[house]
            if lord in planet_positions:
                # Check if lord is in a good house
                lord_house = planet_positions[lord]["HouseNr"]
                if lord_house not in [6, 8, 12]:  # Not in dusthanas
                    strong_education_lords += 1

    if strong_education_lords >= 2:
        intellectual_yogas.append({
            "name": "Vidya Yoga",
            "description": f"Strong lords of education houses, conferring good education and learning abilities."
        })

    # Check for Brahma Yoga - Combination of Jupiter and Mercury with 5th and 9th houses
    if "Jupiter" in planet_positions and "Mercury" in planet_positions:
        jupiter_house = planet_positions["Jupiter"]["HouseNr"]
        mercury_house = planet_positions["Mercury"]["HouseNr"]

        # Check if either planet is in 5th or 9th
        if jupiter_house in [5, 9] or mercury_house in [5, 9]:
            intellectual_yogas.append({
                "name": "Brahma Yoga",
                "description": "Jupiter and Mercury connected with 5th or 9th house, conferring spiritual wisdom and intellectual depth."
            })

        # Check if 5th and 9th lords are with Mercury or Jupiter
        if 5 in house_lords and 9 in house_lords:
            fifth_lord = house_lords[5]
            ninth_lord = house_lords[9]

            if (fifth_lord in planet_positions and ninth_lord in planet_positions):
                fifth_lord_house = planet_positions[fifth_lord]["HouseNr"]
                ninth_lord_house = planet_positions[ninth_lord]["HouseNr"]

                if (fifth_lord_house == jupiter_house or fifth_lord_house == mercury_house or
                    ninth_lord_house == jupiter_house or ninth_lord_house == mercury_house):

                    intellectual_yogas.append({
                        "name": "Brahma Yoga",
                        "description": "Lords of wisdom houses connected with Mercury or Jupiter, conferring deep spiritual knowledge."
                    })

    return intellectual_yogas

def check_malefic_yogas(planet_positions, houses_data):
    """
    Check for important malefic yogas.

    Args:
        planet_positions: Dictionary mapping planet names to their positional data
        houses_data: Dictionary mapping house numbers to house data

    Returns:
        List of dictionaries containing yoga names and descriptions
    """
    malefic_yogas = []

    # Check for Grahan Yoga - Sun/Moon with Rahu/Ketu
    nodes = ["Rahu", "Ketu"]
    luminaries = ["Sun", "Moon"]

    for luminary in luminaries:
        if luminary in planet_positions:
            luminary_house = planet_positions[luminary]["HouseNr"]

            for node in nodes:
                if node in planet_positions and planet_positions[node]["HouseNr"] == luminary_house:
                    malefic_yogas.append({
                        "name": "Grahan Yoga",
                        "description": f"{luminary} conjunct with {node}, indicating karmic challenges or past-life influences."
                    })

    # Check for Kemadruma Yoga - already implemented in other_yogas
    # But let's check it slightly differently here
    if "Moon" in planet_positions:
        moon_house = planet_positions["Moon"]["HouseNr"]

        # Check if Moon is not aspected by any planet and not conjunct any planet
        has_aspect = False
        for planet, data in planet_positions.items():
            if planet == "Moon":
                continue

            # Check for conjunction
            if data["HouseNr"] == moon_house:
                has_aspect = True
                break

            # Check for aspects (simplified)
            planet_house = data["HouseNr"]
            if planet in ["Mars", "Jupiter", "Saturn"]:
                # These planets have special aspects
                if ((planet_house + 3) % 12 == moon_house or  # 4th aspect
                    (planet_house + 6) % 12 == moon_house or  # 7th aspect
                    (planet_house + 7) % 12 == moon_house):  # 8th aspect (for Mars)
                    has_aspect = True
                    break

            # All planets aspect the 7th house
            if (planet_house + 6) % 12 == moon_house:
                has_aspect = True
                break

        if not has_aspect:
            malefic_yogas.append({
                "name": "Kemadruma Yoga",
                "description": "Moon is not aspected by or conjunct with any planet, causing potential isolation or instability."
            })

    # Check for Shakata Yoga - Moon and Jupiter in 6/8 position
    if "Moon" in planet_positions and "Jupiter" in planet_positions:
        moon_house = planet_positions["Moon"]["HouseNr"]
        jupiter_house = planet_positions["Jupiter"]["HouseNr"]

        # Check if they're in 6/8 position to each other
        if abs(moon_house - jupiter_house) == 5 or abs(moon_house - jupiter_house) == 7:
            malefic_yogas.append({
                "name": "Shakata Yoga",
                "description": "Moon and Jupiter in 6/8 position to each other, causing ups and downs in life and emotional challenges."
            })

    # Check for Daridra Yoga - 5th and 9th lords in 6th, 8th, or 12th houses
    house_lords = {}
    for house_num in range(1, 13):
        if house_num in houses_data:
            house_lords[house_num] = houses_data[house_num]["RasiLord"]

    if 5 in house_lords and 9 in house_lords:
        fifth_lord = house_lords[5]
        ninth_lord = house_lords[9]

        if fifth_lord in planet_positions and ninth_lord in planet_positions:
            fifth_lord_house = planet_positions[fifth_lord]["HouseNr"]
            ninth_lord_house = planet_positions[ninth_lord]["HouseNr"]

            if (fifth_lord_house in [6, 8, 12] and ninth_lord_house in [6, 8, 12]):
                malefic_yogas.append({
                    "name": "Daridra Yoga",
                    "description": "Lords of 5th and 9th houses in 6th, 8th or 12th houses, causing financial difficulties."
                })

    # Check for Pitra Dosha - Sun afflicted by malefics
    if "Sun" in planet_positions:
        sun_house = planet_positions["Sun"]["HouseNr"]
        malefics = ["Saturn", "Mars", "Rahu", "Ketu"]

        sun_afflicted = False
        for malefic in malefics:
            if malefic in planet_positions:
                # Check for conjunction
                if planet_positions[malefic]["HouseNr"] == sun_house:
                    sun_afflicted = True
                    break

                # Check for aspect
                malefic_house = planet_positions[malefic]["HouseNr"]
                if malefic == "Saturn" or malefic == "Mars":
                    if ((malefic_house + 3) % 12 == sun_house or  # 4th aspect
                        (malefic_house + 6) % 12 == sun_house or  # 7th aspect
                        (malefic_house + 9) % 12 == sun_house):  # 10th aspect (for Saturn)
                        sun_afflicted = True
                        break

        if sun_afflicted:
            malefic_yogas.append({
                "name": "Pitra Dosha",
                "description": "Sun afflicted by malefics, indicating ancestral karmic issues or difficulties with father/authority figures."
            })

    # Check for Kaal Sarp Dosha - modified version of Kala Sarpa Yoga
    # Already implemented in other_yogas

    return malefic_yogas
