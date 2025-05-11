@app.post("/get_astrocartography_data")
async def get_astrocartography_data(horo_input: ChartInput, planets: List[str] = None):
    """
    Generate astrocartography data for a birth chart.
    Returns planetary lines data suitable for rendering on a world map.

    Parameters:
    ----------
    horo_input: ChartInput
        The chart input data (birth details)
    planets: List[str], optional
        List of planets to include in the analysis. If None, all major planets are included.

    Returns:
    -------
    JSON response containing astrocartography data:
        - status: Success or error status
        - birthLocation: The birth location coordinates
        - lines: Array of planetary line data for mapping
    """
    try:


        # Create a VedicHoroscopeData object from the input
        horoscope = VedicAstro.VedicHoroscopeData(
            year=horo_input.year,
            month=horo_input.month,
            day=horo_input.day,
            hour=horo_input.hour,
            minute=horo_input.minute,
            second=horo_input.second,
            latitude=horo_input.latitude,
            longitude=horo_input.longitude,
            tz=horo_input.utc,
            ayanamsa=horo_input.ayanamsa,
            house_system=horo_input.house_system
        )

        # Create an AstrocartographyCalculator instance
        try:
            astrocartography = AstrocartographyCalculator(horoscope)
            print("Successfully created AstrocartographyCalculator")
        except Exception as e:
            print(f"Error creating AstrocartographyCalculator: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {"status": "error", "message": f"Error initializing astrocartography: {str(e)}"}

        # Process the planets list if provided
        planet_list = None
        if planets:
            print(f"Processing planets list: {planets}")
            # Convert common name formats to flatlib planet constants
            planet_mapping = {
                "sun": const.SUN,
                "moon": const.MOON,
                "mercury": const.MERCURY,
                "venus": const.VENUS,
                "mars": const.MARS,
                "jupiter": const.JUPITER,
                "saturn": const.SATURN,
                "uranus": const.URANUS,
                "neptune": const.NEPTUNE,
                "pluto": const.PLUTO,
                "rahu": const.NORTH_NODE,
                "ketu": const.SOUTH_NODE,
                "north node": const.NORTH_NODE,
                "south node": const.SOUTH_NODE,
                # Add capitalized versions too
                "Sun": const.SUN,
                "Moon": const.MOON,
                "Mercury": const.MERCURY,
                "Venus": const.VENUS,
                "Mars": const.MARS,
                "Jupiter": const.JUPITER,
                "Saturn": const.SATURN,
                "Uranus": const.URANUS,
                "Neptune": const.NEPTUNE,
                "Pluto": const.PLUTO,
                "Rahu": const.NORTH_NODE,
                "Ketu": const.SOUTH_NODE,
                "North Node": const.NORTH_NODE,
                "South Node": const.SOUTH_NODE
            }

            try:
                planet_list = []
                for p in planets:
                    if isinstance(p, str):
                        # First try direct mapping
                        if p in planet_mapping:
                            planet_list.append(planet_mapping[p])
                        else:
                            # Try case-insensitive match if direct mapping fails
                            p_lower = p.lower()
                            if p_lower in planet_mapping:
                                planet_list.append(planet_mapping[p_lower])
                            else:
                                print(f"Warning: Unknown planet '{p}', skipping")

                if not planet_list:
                    print("No valid planets found, using default planets")
                    planet_list = None
                else:
                    print(f"Mapped planets: {planet_list}")
            except Exception as e:
                print(f"Error mapping planets: {str(e)}")
                planet_list = None

        # Get the astrocartography data
        try:
            astro_data = astrocartography.get_astrocartography_data(planet_list)
            print("Successfully calculated astrocartography data")
            return astro_data
        except Exception as e:
            print(f"Error calculating astrocartography data: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {"status": "error", "message": f"Error calculating astrocartography data: {str(e)}"}

    except Exception as e:
        print(f"Unexpected error in get_astrocartography_data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}

@app.post("/get_yogas")
async def get_yogas(horo_input: ChartInput, categorize_by_influence: bool = False):
    """
    Analyzes a birth chart to identify important Hindu astrological yogas (planetary combinations).
    Returns a list of yogas present in the chart with descriptions.

    Args:
        horo_input: Chart input data
        categorize_by_influence: If True, yogas will be categorized as benefic or malefic
                               If False (default), yogas will be categorized by traditional types
    """
    # First get the KP data which contains all planetary positions we need
    kp_data = await get_kp_data(horo_input)

    # Get the rasi chart data which uses Lahiri ayanamsa
    rasi_chart_data = kp_data["rasi_chart"]

    # Create consolidated planet positions directly from rasi chart data
    # This is more accurate for yoga calculations as it properly reflects
    # the sidereal zodiac positions
    planet_positions = {}
    houses_data = {house["HouseNr"]: house for house in kp_data["cusps"]}

    # Define sign rulerships according to Vedic astrology
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

    # Process the rasi chart data to create a proper planet_positions dictionary
    for sign_data in rasi_chart_data:
        rasi = sign_data["Rasi"]
        for planet_entry in sign_data["Planets"]:
            planet_name = planet_entry["Name"]

            # Find which house this planet is in
            house_nr = None
            for house_num, house_data in houses_data.items():
                if house_data["Rasi"] == rasi:
                    house_nr = house_num
                    break

            # If house not found, use a fallback method from planets data
            if house_nr is None:
                for planet in kp_data["planets"]:
                    if planet["Object"] == planet_name:
                        house_nr = planet["HouseNr"]
                        break

            # Skip if we couldn't determine the house
            if house_nr is None:
                continue

            # Gather retrograde information from planets data
            is_retrograde = False
            for planet in kp_data["planets"]:
                if planet["Object"] == planet_name:
                    is_retrograde = planet["isRetroGrade"]
                    break

            planet_positions[planet_name] = {
                "Object": planet_name,
                "Rasi": rasi,
                "RasiLord": sign_lords.get(rasi, ""),  # Add the rasi lord for each planet
                "HouseNr": house_nr,
                "isRetroGrade": is_retrograde,
                # Include other necessary data for yoga calculations
                "SignLonDecDeg": planet_entry.get("SignLonDecDeg", 0),
                "LonDecDeg": planet_entry.get("LonDecDeg", 0)
            }

    # Enhance houses_data with proper rasi lord information
    for house_num, house_data in houses_data.items():
        rasi = house_data["Rasi"]
        houses_data[house_num]["RasiLord"] = sign_lords.get(rasi, "")

    # Get all yoga results by traditional categories
    traditional_yogas = {
        "raj_yogas": check_raj_yogas(planet_positions, houses_data),
        "dhana_yogas": check_dhana_yogas(planet_positions, houses_data),
        "pancha_mahapurusha_yogas": check_pancha_mahapurusha_yogas(planet_positions),
        "nabhasa_yogas": check_nabhasa_yogas(planet_positions),
        "other_yogas": check_other_yogas(planet_positions, houses_data),
        "additional_benefic_yogas": check_additional_benefic_yogas(planet_positions, houses_data),
        "intellectual_yogas": check_intellectual_yogas(planet_positions, houses_data),
        "malefic_yogas": check_malefic_yogas(planet_positions, houses_data)
    }

    # If requested, recategorize yogas by their influence (benefic or malefic)
    if categorize_by_influence:
        benefic_yogas = []
        malefic_yogas = []

        # Categorize traditional yogas by influence
        benefic_categories = ["raj_yogas", "dhana_yogas", "pancha_mahapurusha_yogas",
                            "additional_benefic_yogas", "intellectual_yogas", "other_yogas"]

        for category in benefic_categories:
            for yoga in traditional_yogas[category]:
                # Skip some yogas from other_yogas that are actually malefic
                if category == "other_yogas" and yoga["name"] in ["Kemadruma Yoga", "Kala Sarpa Yoga", "Shakata Yoga"]:
                    malefic_yogas.append(yoga)
                else:
                    benefic_yogas.append(yoga)

        # Add malefic yogas
        malefic_yogas.extend(traditional_yogas["malefic_yogas"])

        # Some Nabhasa yogas can be either benefic or malefic depending on planets involved
        # For simplicity, we'll add them to benefic category
        benefic_yogas.extend(traditional_yogas["nabhasa_yogas"])

        # Return yogas categorized by influence
        return {
            "benefic_yogas": benefic_yogas,
            "malefic_yogas": malefic_yogas,
            "total_yogas": len(benefic_yogas) + len(malefic_yogas)
        }

    # Return yogas categorized by traditional types
    return traditional_yogas

