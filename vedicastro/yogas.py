"""
This module contains functions for analyzing various Vedic astrological yogas.
Yogas are specific planetary combinations that indicate particular effects
in a person's life according to Hindu astrology.
"""

def check_raj_yogas(planet_positions, houses_data):
    """Check for Raj Yogas (combinations for power and authority)"""
    raj_yogas = []

    # Get lords of key houses
    house_lords = {}
    for house_num in range(1, 13):
        if house_num in houses_data:
            house_lords[house_num] = houses_data[house_num]["RasiLord"]

    # Check for Gaja Kesari Yoga - Jupiter in angle from Moon
    if "Moon" in planet_positions and "Jupiter" in planet_positions:
        moon_house = planet_positions["Moon"]["HouseNr"]
        jupiter_house = planet_positions["Jupiter"]["HouseNr"]
        if abs(moon_house - jupiter_house) % 3 == 0:  # 1, 4, 7, 10 houses apart
            raj_yogas.append({
                "name": "Gaja Kesari Yoga",
                "description": "Jupiter is in quadrant from Moon, conferring leadership qualities, fame, and success."
            })

    # Check for Budha-Aditya Yoga - Sun and Mercury in same house
    if "Sun" in planet_positions and "Mercury" in planet_positions:
        sun_house = planet_positions["Sun"]["HouseNr"]
        mercury_house = planet_positions["Mercury"]["HouseNr"]
        if sun_house == mercury_house:
            raj_yogas.append({
                "name": "Budha-Aditya Yoga",
                "description": "Sun and Mercury in same house, conferring intelligence, leadership, and political success."
            })

    # Check for Amala Yoga - 10th from Moon has benefic
    if "Moon" in planet_positions:
        moon_house = planet_positions["Moon"]["HouseNr"]
        tenth_from_moon = (moon_house + 9) % 12 or 12  # 10th house from Moon

        benefics = ["Jupiter", "Venus", "Mercury"]
        for benefic in benefics:
            if benefic in planet_positions and planet_positions[benefic]["HouseNr"] == tenth_from_moon:
                raj_yogas.append({
                    "name": "Amala Yoga",
                    "description": f"Benefic {benefic} in 10th from Moon creates Amala Yoga, conferring pure reputation and authority."
                })

    # Check for Amala Yoga from Lagna - 10th from Lagna has benefic
    benefics = ["Jupiter", "Venus", "Mercury"]
    for benefic in benefics:
        if benefic in planet_positions and planet_positions[benefic]["HouseNr"] == 10:
            raj_yogas.append({
                "name": "Amala Yoga",
                "description": f"Benefic {benefic} in 10th house creates Amala Yoga, conferring pure reputation and authority."
            })

    # Check for Dharma-Karmadhipati Yoga - 9th and 10th lord conjunction
    if 9 in house_lords and 10 in house_lords:
        ninth_lord = house_lords[9]
        tenth_lord = house_lords[10]

        if ninth_lord in planet_positions and tenth_lord in planet_positions:
            ninth_lord_house = planet_positions[ninth_lord]["HouseNr"]
            tenth_lord_house = planet_positions[tenth_lord]["HouseNr"]

            if ninth_lord_house == tenth_lord_house:
                raj_yogas.append({
                    "name": "Dharma-Karmadhipati Yoga",
                    "description": "Lords of 9th and 10th houses conjoined, conferring significant political power and authority."
                })

        # Check if 9th lord is in 10th house (direct Dharma-Karma yoga)
        if ninth_lord in planet_positions and planet_positions[ninth_lord]["HouseNr"] == 10:
            raj_yogas.append({
                "name": "Dharma-Karmadhipati Yoga",
                "description": "9th lord in 10th house, creating direct Dharma-Karma Yoga for success in career and authority."
            })

        # Check if 10th lord is in 9th house
        if tenth_lord in planet_positions and planet_positions[tenth_lord]["HouseNr"] == 9:
            raj_yogas.append({
                "name": "Dharma-Karmadhipati Yoga",
                "description": "10th lord in 9th house, creating direct Dharma-Karma Yoga for success and authority."
            })

    # Check for Parvata Yoga - Benefics in kendras and no malefics in kendras
    kendras = [1, 4, 7, 10]  # Angular houses
    benefics = ["Jupiter", "Venus", "Mercury", "Moon"]
    malefics = ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]

    benefics_in_kendras = False
    malefics_in_kendras = False

    # Check if at least one benefic is in a kendra
    for benefic in benefics:
        if benefic in planet_positions and planet_positions[benefic]["HouseNr"] in kendras:
            benefics_in_kendras = True
            break

    # Check if any malefic is in a kendra
    for malefic in malefics:
        if malefic in planet_positions and planet_positions[malefic]["HouseNr"] in kendras:
            malefics_in_kendras = True
            break

    if benefics_in_kendras and not malefics_in_kendras:
        raj_yogas.append({
            "name": "Parvata Yoga",
            "description": "Benefics in angular houses with no malefics, promising fame, reputation, and prosperity."
        })

    # General Raj yoga check - Kendra and Trikona lords conjoined in any house
    kendras = [1, 4, 7, 10]
    trikonas = [1, 5, 9]

    kendra_lords = [house_lords.get(house) for house in kendras if house in house_lords]
    trikona_lords = [house_lords.get(house) for house in trikonas if house in house_lords]

    # Remove duplicates and None values
    kendra_lords = [lord for lord in kendra_lords if lord]
    trikona_lords = [lord for lord in trikona_lords if lord]

    # Check for Raj Yoga through conjunction
    for kendra_lord in kendra_lords:
        if kendra_lord in planet_positions:
            kendra_lord_house = planet_positions[kendra_lord]["HouseNr"]

            for trikona_lord in trikona_lords:
                if (trikona_lord in planet_positions and
                    trikona_lord != kendra_lord and  # Different lords
                    planet_positions[trikona_lord]["HouseNr"] == kendra_lord_house):  # Same house

                    raj_yogas.append({
                        "name": "Raj Yoga",
                        "description": f"Lords of kendra ({kendra_lord}) and trikona ({trikona_lord}) conjoined, creating powerful Raja Yoga."
                    })

    # Check for Kahala Yoga - 4th and 9th lords strong/in kendra/trikona
    if 4 in house_lords and 9 in house_lords:
        fourth_lord = house_lords[4]
        ninth_lord = house_lords[9]

        if (fourth_lord in planet_positions and ninth_lord in planet_positions):
            fourth_lord_house = planet_positions[fourth_lord]["HouseNr"]
            ninth_lord_house = planet_positions[ninth_lord]["HouseNr"]

            # Check if both are in kendra or trikona houses
            if (fourth_lord_house in kendras + trikonas and
                ninth_lord_house in kendras + trikonas):

                raj_yogas.append({
                    "name": "Kahala Yoga",
                    "description": "Lords of 4th and 9th houses well-placed, conferring courage, leadership, and success."
                })

    return raj_yogas

def check_dhana_yogas(planet_positions, houses_data):
    """Check for Dhana Yogas (combinations for wealth)"""
    dhana_yogas = []

    # Get lords of key houses
    house_lords = {}
    for house_num in range(1, 13):
        if house_num in houses_data:
            house_lords[house_num] = houses_data[house_num]["RasiLord"]

    # Check for Lakshmi Yoga - 9th lord in own house or exalted
    if 9 in house_lords:
        ninth_lord = house_lords[9]
        if ninth_lord in planet_positions:
            planet_data = planet_positions[ninth_lord]
            rasi = planet_data["Rasi"]

            # Exaltation signs for planets
            exaltation_signs = {
                "Sun": "Aries",
                "Moon": "Taurus",
                "Mercury": "Virgo",
                "Venus": "Pisces",
                "Mars": "Capricorn",
                "Jupiter": "Cancer",
                "Saturn": "Libra"
            }

            # Own signs for planets (simplified)
            own_signs = {
                "Sun": ["Leo"],
                "Moon": ["Cancer"],
                "Mercury": ["Gemini", "Virgo"],
                "Venus": ["Taurus", "Libra"],
                "Mars": ["Aries", "Scorpio"],
                "Jupiter": ["Sagittarius", "Pisces"],
                "Saturn": ["Capricorn", "Aquarius"]
            }

            # Check if 9th lord is in own sign or exalted
            is_exalted = exaltation_signs.get(ninth_lord) == rasi
            is_own_sign = rasi in own_signs.get(ninth_lord, [])

            if is_exalted or is_own_sign:
                # Check if Venus is in a kendra or trikona
                venus_in_good_house = False
                if "Venus" in planet_positions:
                    venus_house = planet_positions["Venus"]["HouseNr"]
                    if venus_house in [1, 4, 5, 7, 9, 10]:
                        venus_in_good_house = True

                # Simplified Lakshmi Yoga - just check 9th lord
                dhana_yogas.append({
                    "name": "Lakshmi Yoga",
                    "description": f"9th lord {ninth_lord} in {'exalted' if is_exalted else 'own'} sign, {'' if venus_in_good_house else 'partially '} forming Lakshmi Yoga for wealth and prosperity."
                })

    # Check for Dhana Yoga - 2nd and 11th lord conjunction
    if 2 in house_lords and 11 in house_lords:
        second_lord = house_lords[2]
        eleventh_lord = house_lords[11]

        if second_lord in planet_positions and eleventh_lord in planet_positions:
            second_lord_house = planet_positions[second_lord]["HouseNr"]
            eleventh_lord_house = planet_positions[eleventh_lord]["HouseNr"]

            if second_lord_house == eleventh_lord_house:
                dhana_yogas.append({
                    "name": "Dhana Yoga",
                    "description": "Lords of 2nd and 11th houses conjoined, conferring significant wealth and financial stability."
                })

    # Check for Dhana Yoga - 11th lord in 11th house
    if 11 in house_lords:
        eleventh_lord = house_lords[11]
        if eleventh_lord in planet_positions and planet_positions[eleventh_lord]["HouseNr"] == 11:
            dhana_yogas.append({
                "name": "Dhana Yoga",
                "description": f"11th lord {eleventh_lord} in 11th house, creating a strong wealth yoga."
            })

    # Check for Dhana Yoga - 5th lord in 5th house
    if 5 in house_lords:
        fifth_lord = house_lords[5]
        if fifth_lord in planet_positions and planet_positions[fifth_lord]["HouseNr"] == 5:
            dhana_yogas.append({
                "name": "Dhana Yoga",
                "description": f"5th lord {fifth_lord} in 5th house, creating a wealth yoga through investments and speculation."
            })

    # Check for Dhana Yoga - 9th lord in 10th house
    if 9 in house_lords:
        ninth_lord = house_lords[9]
        if ninth_lord in planet_positions and planet_positions[ninth_lord]["HouseNr"] == 10:
            dhana_yogas.append({
                "name": "Dhana Yoga",
                "description": f"9th lord {ninth_lord} in 10th house, creating wealth through career and fortune."
            })

    # Check for Dhana Yoga - Rahu in 2nd house
    if "Rahu" in planet_positions and planet_positions["Rahu"]["HouseNr"] == 2:
        dhana_yogas.append({
            "name": "Dhana Yoga",
            "description": "Rahu in 2nd house can create sudden wealth and financial gains."
        })

    # Check for Chandra-Mangal Yoga - Moon and Mars relationship
    if "Moon" in planet_positions and "Mars" in planet_positions:
        moon_house = planet_positions["Moon"]["HouseNr"]
        mars_house = planet_positions["Mars"]["HouseNr"]

        # Check if Mars and Moon are in same house
        same_house = moon_house == mars_house

        # Check if they aspect each other (simplified check for trines)
        # In Vedic astrology, houses 5 and 9 from each other (trine)
        trine_aspect = ((moon_house - mars_house) % 12 == 4 or (moon_house - mars_house) % 12 == 8 or
                        (mars_house - moon_house) % 12 == 4 or (mars_house - moon_house) % 12 == 8)

        # Check for mutual aspect or conjunction
        if same_house or trine_aspect:
            dhana_yogas.append({
                "name": "Chandra-Mangal Yoga",
                "description": "Moon and Mars in significant relationship, conferring wealth, business success, and entrepreneurial abilities."
            })

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

            dhana_yogas.append({
                "name": "Saraswati Yoga",
                "description": "Jupiter, Venus and Mercury in angles/trines, conferring wisdom, wealth, and creativity."
            })

    return dhana_yogas

def check_pancha_mahapurusha_yogas(planet_positions):
    """Check for Pancha Mahapurusha Yogas (five great person yogas)"""
    mahapurusha_yogas = []

    # Definitions for exaltation, own sign, and quadrant houses
    quadrant_houses = [1, 4, 7, 10]

    # Check for Ruchaka Yoga - Mars in own sign (Aries/Scorpio) or exalted (Capricorn) in a quadrant
    if "Mars" in planet_positions:
        mars_house = planet_positions["Mars"]["HouseNr"]
        mars_sign = planet_positions["Mars"]["Rasi"]

        if mars_house in quadrant_houses and mars_sign in ["Aries", "Scorpio", "Capricorn"]:
            mahapurusha_yogas.append({
                "name": "Ruchaka Yoga",
                "description": "Mars in own or exalted sign in a quadrant, conferring military prowess, courage, and leadership."
            })

    # Check for Bhadra Yoga - Mercury in own sign (Gemini/Virgo) or exalted (Virgo) in a quadrant
    if "Mercury" in planet_positions:
        mercury_house = planet_positions["Mercury"]["HouseNr"]
        mercury_sign = planet_positions["Mercury"]["Rasi"]

        if mercury_house in quadrant_houses and mercury_sign in ["Gemini", "Virgo"]:
            mahapurusha_yogas.append({
                "name": "Bhadra Yoga",
                "description": "Mercury in own or exalted sign in a quadrant, conferring intelligence, business acumen, and communication skills."
            })

    # Check for Hamsa Yoga - Jupiter in own sign (Sagittarius/Pisces) or exalted (Cancer) in a quadrant
    if "Jupiter" in planet_positions:
        jupiter_house = planet_positions["Jupiter"]["HouseNr"]
        jupiter_sign = planet_positions["Jupiter"]["Rasi"]

        if jupiter_house in quadrant_houses and jupiter_sign in ["Sagittarius", "Pisces", "Cancer"]:
            mahapurusha_yogas.append({
                "name": "Hamsa Yoga",
                "description": "Jupiter in own or exalted sign in a quadrant, conferring wisdom, spirituality, and good fortune."
            })

    # Check for Malavya Yoga - Venus in own sign (Taurus/Libra) or exalted (Pisces) in a quadrant
    if "Venus" in planet_positions:
        venus_house = planet_positions["Venus"]["HouseNr"]
        venus_sign = planet_positions["Venus"]["Rasi"]

        if venus_house in quadrant_houses and venus_sign in ["Taurus", "Libra", "Pisces"]:
            mahapurusha_yogas.append({
                "name": "Malavya Yoga",
                "description": "Venus in own or exalted sign in a quadrant, conferring beauty, artistic talents, luxury, and relationship skills."
            })

    # Check for Sasa Yoga - Saturn in own sign (Capricorn/Aquarius) or exalted (Libra) in a quadrant
    if "Saturn" in planet_positions:
        saturn_house = planet_positions["Saturn"]["HouseNr"]
        saturn_sign = planet_positions["Saturn"]["Rasi"]

        if saturn_house in quadrant_houses and saturn_sign in ["Capricorn", "Aquarius", "Libra"]:
            mahapurusha_yogas.append({
                "name": "Sasa Yoga",
                "description": "Saturn in own or exalted sign in a quadrant, conferring discipline, longevity, and professional success."
            })

    return mahapurusha_yogas

def check_nabhasa_yogas(planet_positions):
    """Check for Nabhasa Yogas (special planetary patterns)"""
    nabhasa_yogas = []

    # Create a count of planets per house
    planets_in_houses = {}
    for planet, data in planet_positions.items():
        house = data["HouseNr"]
        if house not in planets_in_houses:
            planets_in_houses[house] = []
        planets_in_houses[house].append(planet)

    # Check for Shakat Yoga - Moon opposite to Jupiter
    if "Moon" in planet_positions and "Jupiter" in planet_positions:
        moon_house = planet_positions["Moon"]["HouseNr"]
        jupiter_house = planet_positions["Jupiter"]["HouseNr"]

        if abs(moon_house - jupiter_house) == 6:  # 7 houses apart (opposite)
            nabhasa_yogas.append({
                "name": "Shakat Yoga",
                "description": "Moon opposite to Jupiter, which can create obstacles and challenges."
            })

    # Check for Yuga Yoga - all seven classical planets in six consecutive signs
    # Get the signs (Rasis) occupied by the classical planets
    classical_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    occupied_signs = set()
    planets_found = 0

    for planet in classical_planets:
        if planet in planet_positions:
            planets_found += 1
            occupied_signs.add(planet_positions[planet]["Rasi"])

    # Only check for Yuga Yoga if all classical planets are present
    if planets_found == 7:
        # Check if the signs can form a sequence of 6 consecutive signs
        zodiac_signs = [
            "Aries", "Taurus", "Gemini", "Cancer",
            "Leo", "Virgo", "Libra", "Scorpio",
            "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]

        # Try each sign as a potential starting point
        for start_idx in range(12):
            consecutive_count = 0
            for offset in range(6):  # Check for 6 consecutive signs
                current_sign = zodiac_signs[(start_idx + offset) % 12]
                if current_sign in occupied_signs:
                    consecutive_count += 1

            # If all occupied signs are within 6 consecutive signs
            if len(occupied_signs) <= 6 and consecutive_count == len(occupied_signs):
                nabhasa_yogas.append({
                    "name": "Yuga Yoga",
                    "description": "All seven classical planets occupy six or fewer consecutive signs, conferring versatility, leadership, and success in collaborative efforts."
                })
                break

    # Check for Rajju Yoga - planets aligned in specific houses
    rajju_types = [
        ([1, 5, 9], "Adhomukha Rajju"),
        ([2, 6, 10], "Madhyamukha Rajju"),
        ([3, 7, 11], "Oordhwamukha Rajju"),
        ([4, 8, 12], "Parshwa Rajju")
    ]

    for house_group, rajju_name in rajju_types:
        planets_in_group = []
        for house in house_group:
            if house in planets_in_houses:
                planets_in_group.extend(planets_in_houses[house])

        if len(planets_in_group) >= 5:  # If 5 or more planets are in the pattern
            nabhasa_yogas.append({
                "name": f"{rajju_name} Yoga",
                "description": f"Five or more planets in {house_group} houses, creating a specific pattern of effects."
            })

    return nabhasa_yogas

def check_other_yogas(planet_positions, houses_data):
    """Check for other important yogas"""
    other_yogas = []

    # Check for Neechabhanga Raj Yoga - debilitated planet receiving cancellation
    # This is a simplified check; would need complete debilitation signs in a full implementation
    debilitation_signs = {
        "Sun": "Libra",
        "Moon": "Scorpio",
        "Mars": "Cancer",
        "Mercury": "Pisces",
        "Jupiter": "Capricorn",
        "Venus": "Virgo",
        "Saturn": "Aries"
    }

    for planet, debi_sign in debilitation_signs.items():
        if planet in planet_positions and planet_positions[planet]["Rasi"] == debi_sign:
            # Check if the lord of the sign is in a quadrant or trine
            sign_lord = ""
            for sign_lord_candidate in planet_positions:
                if sign_lord_candidate in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
                    if planet_positions[sign_lord_candidate]["HouseNr"] in [1, 4, 5, 7, 9, 10]:
                        sign_lord = sign_lord_candidate
                        break

            if sign_lord:
                other_yogas.append({
                    "name": "Neechabhanga Raj Yoga",
                    "description": f"{planet} is in debilitation but its lord {sign_lord} is in a strong position, cancelling the debilitation and creating powerful effects."
                })

    # Check for Viparita Raja Yoga - malefics in 6th, 8th, or 12th from lagna
    # Enhanced check including lords of 6th, 8th, and 12th houses
    malefics = ["Sun", "Mars", "Saturn", "Rahu"]
    malefics_in_dusthana = []

    for malefic in malefics:
        if malefic in planet_positions and planet_positions[malefic]["HouseNr"] in [6, 8, 12]:
            malefics_in_dusthana.append(malefic)

    # Get lords of key houses
    house_lords = {}
    for house_num in range(1, 13):
        if house_num in houses_data:
            house_lords[house_num] = houses_data[house_num]["RasiLord"]

    # Check for 6th, 8th, and 12th lords in dusthanas
    dusthana_lords = []
    dusthana_houses = [6, 8, 12]

    for dusthana in dusthana_houses:
        if dusthana in house_lords:
            lord = house_lords[dusthana]
            if lord in planet_positions:
                house_of_lord = planet_positions[lord]["HouseNr"]
                if house_of_lord in dusthana_houses:
                    dusthana_lords.append(f"{lord} ({dusthana} lord in {house_of_lord})")

    # Check for Viparita Raja Yoga based on dusthana lords
    if len(dusthana_lords) >= 1:
        other_yogas.append({
            "name": "Viparita Raja Yoga",
            "description": f"Lords of dusthana houses placed in dusthanas: {', '.join(dusthana_lords)}, turning negative influences into positive results."
        })

    # Also check malefics in dusthanas (original check)
    elif len(malefics_in_dusthana) >= 2:
        other_yogas.append({
            "name": "Viparita Raja Yoga",
            "description": f"Malefics {', '.join(malefics_in_dusthana)} in 6th, 8th or 12th houses, turning negative influences into positive results."
        })

    # Check for Gajakesari Yoga (duplicated from Raj Yogas for completeness)
    if "Moon" in planet_positions and "Jupiter" in planet_positions:
        moon_house = planet_positions["Moon"]["HouseNr"]
        jupiter_house = planet_positions["Jupiter"]["HouseNr"]
        if abs(moon_house - jupiter_house) % 3 == 0:  # 1, 4, 7, 10 houses apart
            other_yogas.append({
                "name": "Gajakesari Yoga",
                "description": "Jupiter is in quadrant from Moon, conferring leadership qualities, fame, and success."
            })

    # Check for Kemadruma Yoga - Moon with no planets on either side
    if "Moon" in planet_positions:
        moon_house = planet_positions["Moon"]["HouseNr"]
        prev_house = moon_house - 1 if moon_house > 1 else 12
        next_house = moon_house + 1 if moon_house < 12 else 1

        planets_adjacent = False
        for planet, data in planet_positions.items():
            if planet != "Moon" and (data["HouseNr"] == prev_house or data["HouseNr"] == next_house):
                planets_adjacent = True
                break

        if not planets_adjacent and "Asc" not in [prev_house, next_house]:
            other_yogas.append({
                "name": "Kemadruma Yoga",
                "description": "Moon has no planets or Ascendant in adjacent houses, potentially causing hardships or difficulties."
            })

    # Check for Chandra-Mangal Dhan Yoga - Moon and Mars relationship
    if "Moon" in planet_positions and "Mars" in planet_positions:
        moon_house = planet_positions["Moon"]["HouseNr"]
        mars_house = planet_positions["Mars"]["HouseNr"]

        # Check if Mars aspects Moon (4th, 7th, 8th aspect) or is in same house
        mars_aspects_moon = (
            moon_house == mars_house or  # Same house
            (mars_house + 3) % 12 == moon_house or  # 4th aspect
            (mars_house + 6) % 12 == moon_house or  # 7th aspect
            (mars_house + 7) % 12 == moon_house  # 8th aspect
        )

        if mars_aspects_moon:
            other_yogas.append({
                "name": "Chandra-Mangal Dhan Yoga",
                "description": "Moon and Mars in significant relationship, conferring wealth accumulation and financial gains."
            })

    # Check for Parivartana Yoga - mutual exchange between planets
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

    # Create a mapping of planets to their signs
    planet_in_sign = {}
    for planet, data in planet_positions.items():
        if planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            planet_in_sign[planet] = data["Rasi"]

    # Check for mutual exchange
    parivartanas = []
    for planet1, sign1 in planet_in_sign.items():
        for planet2, sign2 in planet_in_sign.items():
            if planet1 != planet2 and sign_lords.get(sign1) == planet2 and sign_lords.get(sign2) == planet1:
                parivartanas.append((planet1, planet2))

    for planet1, planet2 in parivartanas:
        other_yogas.append({
            "name": "Parivartana Yoga",
            "description": f"Mutual exchange between {planet1} and {planet2}, creating a powerful yoga that strengthens both planets."
        })

    # Check for Kala Sarpa Yoga - all planets between Rahu and Ketu
    if "Rahu" in planet_positions and "Ketu" in planet_positions:
        rahu_house = planet_positions["Rahu"]["HouseNr"]
        ketu_house = planet_positions["Ketu"]["HouseNr"]

        # In Kala Sarpa Yoga, all planets should be on one side of the Rahu-Ketu axis
        planets_outside_axis = False
        for planet, data in planet_positions.items():
            if planet not in ["Rahu", "Ketu"]:
                planet_house = data["HouseNr"]

                # Check if planet is outside the Rahu-Ketu axis
                if rahu_house < ketu_house:  # If Rahu is before Ketu in zodiacal order
                    if planet_house < rahu_house or planet_house > ketu_house:
                        planets_outside_axis = True
                        break
                else:  # If Ketu is before Rahu
                    if planet_house < ketu_house or planet_house > rahu_house:
                        planets_outside_axis = True
                        break

        if not planets_outside_axis:
            other_yogas.append({
                "name": "Kala Sarpa Yoga",
                "description": "All planets are between Rahu and Ketu, indicating karmic challenges but also significant spiritual growth potential."
            })

    # Check for Kendra-Trikona Yoga - lords of kendras and trikonas conjunct or exchange
    kendra_houses = [1, 4, 7, 10]  # Angular houses
    trikona_houses = [1, 5, 9]  # Trine houses

    # Get lords of kendras and trikonas
    kendra_lords = [house_lords.get(house) for house in kendra_houses if house in house_lords]
    trikona_lords = [house_lords.get(house) for house in trikona_houses if house in house_lords]

    # Check for conjunction between lords
    for kendra_lord in kendra_lords:
        if kendra_lord and kendra_lord in planet_positions:
            kendra_lord_house = planet_positions[kendra_lord]["HouseNr"]

            for trikona_lord in trikona_lords:
                if (trikona_lord and trikona_lord in planet_positions and
                    trikona_lord != kendra_lord and
                    planet_positions[trikona_lord]["HouseNr"] == kendra_lord_house):

                    other_yogas.append({
                        "name": "Kendra-Trikona Yoga",
                        "description": f"Lords of kendra ({kendra_lord}) and trikona ({trikona_lord}) are conjunct, creating a powerful Raja Yoga for authority and success."
                    })

    # Check for Trikona-Kendra Yoga - a broader definition looking at trikona lords in kendras
    # This is slightly different from the above as it focuses on placement rather than conjunction
    for trikona_lord in set(trikona_lords):  # Use set to avoid duplicates
        if trikona_lord and trikona_lord in planet_positions:
            trikona_lord_house = planet_positions[trikona_lord]["HouseNr"]

            # If a trikona lord is placed in a kendra house
            if trikona_lord_house in kendra_houses:
                other_yogas.append({
                    "name": "Trikona-Kendra Yoga",
                    "description": f"{trikona_lord} (lord of trikona) is placed in a kendra house ({trikona_lord_house}), creating Raja Yoga."
                })

    # Check for Kendra-Trikona Yoga - a broader definition looking at kendra lords in trikonas
    for kendra_lord in set(kendra_lords):  # Use set to avoid duplicates
        if kendra_lord and kendra_lord in planet_positions:
            kendra_lord_house = planet_positions[kendra_lord]["HouseNr"]

            # If a kendra lord is placed in a trikona house
            if kendra_lord_house in trikona_houses:
                other_yogas.append({
                    "name": "Kendra-Trikona Yoga",
                    "description": f"{kendra_lord} (lord of kendra) is placed in a trikona house ({kendra_lord_house}), creating Raja Yoga."
                })

    # Check for Shakata Yoga - Moon and Jupiter in 6/8 position
    if "Moon" in planet_positions and "Jupiter" in planet_positions:
        moon_house = planet_positions["Moon"]["HouseNr"]
        jupiter_house = planet_positions["Jupiter"]["HouseNr"]

        # Check if they're in 6/8 position to each other
        if abs(moon_house - jupiter_house) == 5 or abs(moon_house - jupiter_house) == 7:
            other_yogas.append({
                "name": "Shakata Yoga",
                "description": "Moon and Jupiter in 6/8 position to each other, causing ups and downs in life and emotional challenges."
            })

    # Check for Vesi Yoga - planet in 2nd from Sun
    if "Sun" in planet_positions:
        sun_house = planet_positions["Sun"]["HouseNr"]
        second_from_sun = (sun_house + 1) % 12 or 12  # 2nd house from Sun

        for planet, data in planet_positions.items():
            if planet != "Sun" and planet != "Moon" and data["HouseNr"] == second_from_sun:
                other_yogas.append({
                    "name": "Vesi Yoga",
                    "description": f"{planet} in 2nd from Sun, giving power of speech and persuasion."
                })

    # Check for Shubha Vesi Yoga - Benefic in 2nd from Sun
    if "Sun" in planet_positions:
        sun_house = planet_positions["Sun"]["HouseNr"]
        second_from_sun = (sun_house + 1) % 12 or 12  # 2nd house from Sun

        benefics = ["Jupiter", "Venus", "Mercury"]
        for benefic in benefics:
            if benefic in planet_positions and planet_positions[benefic]["HouseNr"] == second_from_sun:
                other_yogas.append({
                    "name": "Shubha Vesi Yoga",
                    "description": f"Benefic {benefic} in 2nd from Sun, bringing auspicious speech and eloquence."
                })

    # Check for Ubhayachari Yoga - Planets in both 2nd and 12th from Sun
    if "Sun" in planet_positions:
        sun_house = planet_positions["Sun"]["HouseNr"]
        second_from_sun = (sun_house + 1) % 12 or 12  # 2nd house from Sun
        twelfth_from_sun = (sun_house - 1) if sun_house > 1 else 12  # 12th house from Sun

        planets_in_2nd = []
        planets_in_12th = []

        for planet, data in planet_positions.items():
            if planet != "Sun" and planet != "Moon":
                if data["HouseNr"] == second_from_sun:
                    planets_in_2nd.append(planet)
                if data["HouseNr"] == twelfth_from_sun:
                    planets_in_12th.append(planet)

        if planets_in_2nd and planets_in_12th:
            other_yogas.append({
                "name": "Ubhayachari Yoga",
                "description": f"Planets in both 2nd and 12th from Sun: {', '.join(planets_in_2nd)} in 2nd and {', '.join(planets_in_12th)} in 12th, giving balanced speech and thought."
            })

    return other_yogas
