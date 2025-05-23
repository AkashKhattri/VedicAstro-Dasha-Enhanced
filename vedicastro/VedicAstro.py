from vedicastro.utils import *
from datetime import datetime, timedelta
from flatlib import const
from flatlib.chart import Chart
from flatlib.geopos import GeoPos
from flatlib.datetime import Datetime, Date
from flatlib.object import GenericObject
from flatlib import aspects
import collections
import polars as pl


## GLOBAL VARS
RASHIS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra',
          'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

ROMAN_HOUSE_NUMBERS = {'House1': 'I', 'House2': 'II', 'House3': 'III', 'House4': 'IV', 'House5': 'V', 'House6': 'VI',
                    'House7': 'VII', 'House8': 'VIII', 'House9': 'IX', 'House10': 'X', 'House11': 'XI', 'House12': 'XII'
                    }

## Lords of the 12 Zodiac Signs
SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]

NAKSHATRAS = ['Ashwini','Bharani','Krittika','Rohini','Mrigashīrsha', 'Ardra', 'Punarvasu', 'Pushya', 'Āshleshā',
'Maghā', 'PūrvaPhalgunī', 'UttaraPhalgunī', 'Hasta', 'Chitra', 'Svati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula',
'PurvaAshadha','UttaraAshadha', 'Shravana', 'Dhanishta','Shatabhisha', 'PurvaBhādrapadā', 'UttaraBhādrapadā', 'Revati']

AYANAMSA_MAPPING = { "Lahiri": const.AY_LAHIRI, "Lahiri_1940" : const.AY_LAHIRI_1940,
                    "Lahiri_VP285": const.AY_LAHIRI_VP285, "Lahiri_ICRC" : const.AY_LAHIRI_ICRC, "Raman": const.AY_RAMAN,
                    "Krishnamurti": const.AY_KRISHNAMURTI, "Krishnamurti_Senthilathiban": const.AY_KRISHNAMURTI_SENTHILATHIBAN,
                    }


HOUSE_SYSTEM_MAPPING = { "Placidus": const.HOUSES_PLACIDUS, "Equal": const.HOUSES_EQUAL,
                        "Equal 2": const.HOUSES_EQUAL_2, "Whole Sign": const.HOUSES_WHOLE_SIGN,
                    }

ASPECT_MAPPING = {  const.NO_ASPECT: "No Aspect", const.CONJUNCTION: "Conjunction", const.SEXTILE: "Sextile",
                    const.SQUARE: "Square", const.TRINE: "Trine", const.OPPOSITION: "Opposition",
                    const.SEMISEXTILE: "Semi Sextile", const.SEMIQUINTILE: "Semi Quintile",
                    const.SEMISQUARE: "Semi Square", const.QUINTILE: "Quintile",
                    const.SESQUIQUINTILE: "Sesqui Quintile", const.SESQUISQUARE: "Sesqui Square",
                    const.BIQUINTILE: "Bi Quintile", const.QUINCUNX: "Quincunx",
                    }

# Columns names for NamedTuple Collections / Final Output DataFrames
HOUSES_TABLE_COLS = ["Object", "HouseNr","Rasi", "LonDecDeg", "SignLonDMS", "SignLonDecDeg", "DegSize",
                     "Nakshatra", "RasiLord", "NakshatraLord", "SubLord", "SubSubLord"]

PLANETS_TABLE_COLS = ["Object", "Rasi", "isRetroGrade", "LonDecDeg", "SignLonDMS", "SignLonDecDeg", "LatDMS",
                        "Nakshatra", "RasiLord", "NakshatraLord", "SubLord", "SubSubLord" ,"HouseNr"]


class VedicHoroscopeData:
    def __init__(self, year:int, month:int, day:int, hour:int, minute:int, second : int,
                 latitude:float, longitude:float, tz : str = None, ayanamsa: str = "Krishnamurti", house_system : str = "Placidus"):
        """
        Generates Planetary and House Positions Data for a time and place input.

        Parameters
        ==========
        year: Year input to generate chart, int (Eg: 2024)
        month: Month input to generate chart, int (1 - 12)
        day:  Day of the month input to generate chart, int  (Eg: 1 - 30,31)
        hour: Hour input to generate chart, int  (Eg: 0 - 23)
        minute: Minute input to generate chart, int  (Eg: 0 - 59)
        second: Second input to generate chart, int  (Eg: 0 - 59)
        latitude: latitude, float
        longitude: longitude, float
        time_zone: timezone input to generate chart, str  (Eg: America/New_York)
        ayanamsa: ayanamsa input to generate chart, str
        house: House System to generate chart,
        """
        self.year       = year
        self.month      = month
        self.day        = day
        self.hour       = hour
        self.minute     = minute
        self.second     = second
        self.latitude   = latitude
        self.longitude  = longitude
        self.ayanamsa   = ayanamsa
        self.house_system = house_system
        self.time_zone = tz if tz else TimezoneFinder().timezone_at(lat=self.latitude, lng=self.longitude)
        self.chart_time = datetime(self.year, self.month, self.day, self.hour, self.minute)
        self.utc,_ = get_utc_offset(self.time_zone, self.chart_time)

    def get_ayanamsa(self):
        """Returns an Ayanamsa System from flatlib.sidereal library, based on user input"""
        return AYANAMSA_MAPPING.get(self.ayanamsa, None)

    def get_house_system(self):
        """Returns an House System from flatlib.sidereal library, based on user input"""
        return HOUSE_SYSTEM_MAPPING.get(self.house_system, None)

    def generate_chart(self):
        """Generates a `flatlib.Chart` object for the given time and location data"""
        date = Datetime([self.year, self.month, self.day], ["+",self.hour, self.minute, self.second], self.utc)
        geopos = GeoPos(self.latitude, self.longitude)
        chart = Chart(date, geopos, IDs=const.LIST_OBJECTS, hsys=self.get_house_system(), mode = self.get_ayanamsa())
        return chart

    def get_planetary_aspects(self, chart: Chart):
        """Computes planetary aspects using flatlib modules getAspect"""
        planets = [const.SUN, const.MOON, const.MARS, const.MERCURY, const.JUPITER, const.VENUS, const.SATURN,
                    const.URANUS, const.NEPTUNE, const.PLUTO, const.NORTH_NODE, const.SOUTH_NODE]
        # aspects_output = []
        aspects_dict = []

        for p1 in planets:
            for p2 in planets:
                if p1 != p2:
                    obj1 = chart.get(p1)
                    obj2 = chart.get(p2)
                    aspect = aspects.getAspect(obj1, obj2, const.ALL_ASPECTS)
                    ## Replace North and South nodes with conventional names
                    p1_new = p1.replace("North Node", "Rahu").replace("South Node", "Ketu")
                    p2_new = p2.replace("North Node", "Rahu").replace("South Node", "Ketu")
                    if aspect.exists():
                        aspect_type = ASPECT_MAPPING[int(aspect.type)]  # Use global variable here
                        aspect_orb = round(aspect.orb, 3)  # get the orb value
                        # Calculate longitude difference
                        p1_lon = round(obj1.lon, 3)
                        p2_lon = round(obj2.lon, 3)
                        lon_diff = round(abs(p1_lon - p2_lon), 3)
                        if lon_diff > 180:
                            lon_diff = 360 - lon_diff

                        aspects_dict.append({"P1":p1_new, "P2": p2_new, "AspectType" : aspect_type,
                                            "AspectDeg" : aspect.type, "AspectOrb" : aspect_orb,
                                            "P1_Lon": p1_lon,"P2_Lon": p2_lon,"LonDiff": lon_diff})


        return aspects_dict

    def get_planet_aspects_on_signs(self, chart: Chart):
        """
        Calculates which signs each planet aspects based on Vedic astrology rules (Drishti).
        Returns a dictionary mapping each planet to a list of sign numbers (1-12) it aspects.

        Aspect rules:
        - All planets aspect the 7th sign from their position
        - Jupiter additionally aspects the 5th and 9th signs
        - Mars additionally aspects the 4th and 8th signs
        - Saturn additionally aspects the 3rd and 10th signs
        - Rahu and Ketu aspect the 5th, 7th, and 9th signs (like Jupiter)
        """
        # Define the planets list
        planets = [const.SUN, const.MOON, const.MARS, const.MERCURY, const.JUPITER, const.VENUS,
                   const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO, const.NORTH_NODE, const.SOUTH_NODE]

        # Define the aspect rules for each planet according to Vedic astrology (Drishti)
        aspect_rules = {
            const.SUN: [7],             # Sun aspects 7th sign
            const.MOON: [7],            # Moon aspects 7th sign
            const.MERCURY: [7],         # Mercury aspects 7th sign
            const.VENUS: [7],           # Venus aspects 7th sign
            const.PLUTO: [7],           # Pluto aspects 7th sign (not traditional)
            const.URANUS: [7],          # Uranus aspects 7th sign (not traditional)
            const.NEPTUNE: [7],         # Neptune aspects 7th sign (not traditional)
            const.MARS: [4, 7, 8],      # Mars aspects 4th, 7th, and 8th signs
            const.JUPITER: [5, 7, 9],   # Jupiter aspects 5th, 7th, and 9th signs
            const.SATURN: [3, 7, 10],   # Saturn aspects 3rd, 7th, and 10th signs
            const.NORTH_NODE: [5, 7, 9], # Rahu aspects 5th, 7th, and 9th signs like Jupiter
            const.SOUTH_NODE: [5, 7, 9]  # Ketu aspects 5th, 7th, and 9th signs like Jupiter
        }

        # Initialize the result dictionary
        planet_aspects = {}

        for planet in planets:
            # Get the planet object
            obj = chart.get(planet)

            # Get the sign number (1-12) where the planet is located
            planet_sign = ((int(obj.lon) // 30) + 1)

            # Replace North and South nodes with conventional names
            planet_name = planet.replace("North Node", "Rahu").replace("South Node", "Ketu")

            # Initialize the list of signs this planet aspects
            aspected_signs = []

            # Add signs based on the planet's aspect rules
            for aspect in aspect_rules.get(planet, [7]):  # Default to just 7th aspect
                # Calculate the aspected sign (1-12)
                aspected_sign = ((planet_sign + aspect - 1) % 12) + 1
                aspected_signs.append(aspected_sign)

            # Store the planet's aspected signs in the result dictionary
            planet_aspects[planet_name] = sorted(aspected_signs)

        return planet_aspects

    def get_planetary_aspects_15(self, chart: Chart):
        """
        Computes exact planetary aspects based on multiples of 15 degrees without using flatlib's aspect functions.
        """
        planets = [const.SUN, const.MOON, const.MARS, const.MERCURY, const.JUPITER, const.VENUS, const.SATURN,
                const.URANUS, const.NEPTUNE, const.PLUTO, const.NORTH_NODE, const.SOUTH_NODE]
        aspects_dict = []

        for p1 in planets:
            for p2 in planets:
                if p1 != p2:
                    # Skip Rahu-Ketu pair as they're always 180 degrees apart
                    if {p1, p2} == {const.NORTH_NODE, const.SOUTH_NODE}:
                        continue

                    obj1 = chart.get(p1)
                    obj2 = chart.get(p2)

                    # Replace North and South nodes with conventional names
                    p1_name = p1.replace("North Node", "Rahu").replace("South Node", "Ketu")
                    p2_name = p2.replace("North Node", "Rahu").replace("South Node", "Ketu")

                    p1_lon = round(obj1.lon, 3)
                    p2_lon = round(obj2.lon, 3)
                    lon_diff = abs(p1_lon - p2_lon)
                    if lon_diff > 180:
                        lon_diff = 360 - lon_diff
                    lon_diff = round(lon_diff, 3)

                    # Check if lon_diff is a multiple of 15 degrees with a small tolerance
                    if abs(lon_diff % 15) == 0.0 :

                        aspects_dict.append({
                            "P1": p1_name,
                            "P2": p2_name,
                            "P1_Lon": p1_lon,
                            "P2_Lon": p2_lon,
                            "AspectType": f"{int(lon_diff)}° Aspect",
                            "AspectDeg": lon_diff
                        })

        # Remove duplicate entries using tuple sort
        unique_aspects = {}
        for aspect in aspects_dict:
            planet_pair = tuple(sorted([aspect['P1'], aspect['P2']]))
            if planet_pair not in unique_aspects:
                unique_aspects[planet_pair] = aspect

        return list(unique_aspects.values())

    def get_planetary_aspects_vedic(self, planets_data: collections.namedtuple):
        """
        Computes the major planetary aspects according to Vedic astrology, focusing on the positions of planets in houses and signs.
        """

        # Get the planets data and Filter planets_data to remove objects like "Asc", "Chiron", "Syzygy", "Fortuna"
        planets_data = [planet for planet in planets_data if planet.Object not in ["Asc", "Chiron", "Syzygy", "Fortuna"]]

        # Define Vedic aspect rules based on sign and house positions
        vedic_aspects_rules = {
            'Conjunction': lambda p1, p2: p1.Rasi == p2.Rasi or p1.HouseNr == p2.HouseNr,
            'Opposition': lambda p1, p2: ((RASHIS.index(p1.Rasi) - RASHIS.index(p2.Rasi)) % 12 == 6 or abs(p1.HouseNr - p2.HouseNr) == 6),
            'Trine': lambda p1, p2: ((RASHIS.index(p1.Rasi) - RASHIS.index(p2.Rasi)) % 12 in [4, 8] or abs(p1.HouseNr - p2.HouseNr) in [4, 8]),
            'Square': lambda p1, p2: ((RASHIS.index(p1.Rasi) - RASHIS.index(p2.Rasi)) % 12 in [3, 9] or abs(p1.HouseNr - p2.HouseNr) in [3, 9]),
            'Sextile': lambda p1, p2: ((RASHIS.index(p1.Rasi) - RASHIS.index(p2.Rasi)) % 12 in [2, 10] or abs(p1.HouseNr - p2.HouseNr) in [2, 10])
        }

        aspects_vedic_output = []
        vedic_aspects_dict = []

        # Check each pair of planets for aspects
        for i in range(len(planets_data)):
            for j in range(i + 1, len(planets_data)):
                for aspect_name, check_func in vedic_aspects_rules.items():
                    if check_func(planets_data[i], planets_data[j]):
                        aspects_vedic_output.append(f"{planets_data[i].Object} and {planets_data[j].Object} are in {aspect_name}")
                        vedic_aspects_dict.append({"P1":planets_data[i].Object, "P2": planets_data[j].Object, "Aspect" : aspect_name,
                                                   "P1_HouseNr": planets_data[i].HouseNr, "P2_HouseNr": planets_data[j].HouseNr,
                                                   "P1_Rasi": planets_data[i].Rasi, "P2_Rasi": planets_data[j].Rasi}
                                                   )
        return vedic_aspects_dict, aspects_vedic_output

    def get_ascendant_data(self, asc_data: GenericObject, PlanetsDataCollection : collections.namedtuple):
        """Generates Ascendant Data and returns the data in the format of the PlanetsDataCollection Named Tuple"""
        asc_chart_data = clean_select_objects_split_str(str(asc_data))
        asc_rl_nl_sl_data = self.get_rl_nl_sl_data(deg = asc_data.lon)
        # Create a dictionary with None values for all fields
        data_dict = {field: None for field in PlanetsDataCollection._fields}
        # Update the specific fields with the ascendant data
        data_dict["Object"] = asc_chart_data[0]
        data_dict["Rasi"] = asc_chart_data[1]
        data_dict["SignLonDMS"] = asc_chart_data[2]
        data_dict["Nakshatra"] = asc_rl_nl_sl_data.get("Nakshatra", None)
        data_dict["RasiLord"]  = asc_rl_nl_sl_data.get("RasiLord", None)
        data_dict["SubLord"] = asc_rl_nl_sl_data.get("SubLord", None)
        data_dict["SubSubLord"] = asc_rl_nl_sl_data.get("SubSubLord", None)
        data_dict["NakshatraLord"] = asc_rl_nl_sl_data.get("NakshatraLord", None)
        data_dict["isRetroGrade"] = None
        data_dict["LonDecDeg"] = round(asc_data.lon, 3)
        data_dict["SignLonDecDeg"] = dms_to_decdeg(asc_chart_data[2])
        data_dict["LatDMS"] = None
        data_dict["HouseNr"] = 1

        # Return a new PlanetsDataCollection instance with the data
        return PlanetsDataCollection(**data_dict)

    def get_rl_nl_sl_data(self, deg : float):
        """
        Returns the  Rashi (Sign) Lord, Nakshatra, Nakshatra Pada, Nakshatra Lord, Sub Lord and Sub Sub Lord
        corresponding to the given degree.
        """
        duration = [7, 20, 6, 10, 7, 18, 16, 19, 17]

        lords = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

        star_lords = lords * 3 ## lords for the 27 Nakshatras

        ## Compute Sign lords
        sign_deg = deg % 360  # Normalize degree to [0, 360)
        sign_index = int(sign_deg // 30)  # Each zodiac sign is 30 degrees

        # Compute Nakshatra details
        nakshatra_deg = sign_deg % 13.332  # Each nakshatra is 13.332 degrees
        nakshatra_index = int(sign_deg // 13.332)  # Find the nakshatra index
        pada = int((nakshatra_deg % 13.332) // 3.325) + 1  # Each pada is 3.325 degrees

        # Ensure nakshatra_index is within bounds
        nakshatra_index = nakshatra_index % len(NAKSHATRAS)

        # Compute SubLords
        deg = deg - 120 * int(deg / 120)
        degcum = 0
        i = 0

        while i < 9:
            deg_nl = 360 / 27
            j = i
            while True:
                deg_sl = deg_nl * duration[j] / 120
                k = j
                while True:
                    deg_ss = deg_sl * duration[k] / 120
                    degcum += deg_ss
                    if degcum >= deg:
                        return {"Nakshatra": NAKSHATRAS[nakshatra_index], "Pada": pada,
                                "NakshatraLord": star_lords[nakshatra_index], "RasiLord": SIGN_LORDS[sign_index],
                                "SubLord": lords[j], "SubSubLord": lords[k] }
                    k = (k + 1) % 9
                    if k == j:
                        break
                j = (j + 1) % 9
                if j == i:
                    break
            i += 1


    def get_transit_details(self):
        """
        Captures the rl_nl_sl transit data for all planets at the current chart time.

        Returns
        =======
        A named tuple collection containing the transit details for all planets.
        """
        # Define the named tuple for transit details
        TransitDetails = collections.namedtuple('TransitDetails', [
            'timestamp', 'PlanetName', 'PlanetLon', 'PlanetSign', 'Nakshatra',
            'NakshatraLord', 'SubLord', 'SubLordSign', 'isRetrograde'
        ])
        chart = self.generate_chart()
        transit_data = []
        timestamp = f"{self.year}-{self.month:02d}-{self.day:02d} {self.hour:02d}:{self.minute:02d}:00"
        for planet in chart.objects:
            if planet.id not in ["Chiron", "Syzygy", "Pars Fortuna"]:
                planet_name = clean_select_objects_split_str(str(planet))[0]
                ## Get additional details like Nakshatra, RL, NL, SL details
                rl_nl_sl_data = self.get_rl_nl_sl_data(deg = planet.lon)
                planet_star = rl_nl_sl_data.get("Nakshatra", None)
                planet_star_lord = rl_nl_sl_data.get("NakshatraLord", None)
                planet_sub_lord = rl_nl_sl_data.get("SubLord", None)
                sub_lord_sign = chart.get(planet_sub_lord.replace("Rahu","North Node").replace("Ketu", "South Node")).sign

                ## Append data to NamedTuple Collection
                transit_data.append(TransitDetails(timestamp, planet_name, round(planet.lon,3), planet.sign, planet_star,
                                                planet_star_lord, planet_sub_lord, sub_lord_sign, planet.isRetrograde()))
        return transit_data

    def get_planets_data_from_chart(self, chart: Chart, new_houses_chart: Chart = None):
        """
        Generate the planets data table given a `flatlib.Chart` object.
        Parameters
        ==========
        chart: flatlib Chart object using which planetary positions have to be generated
        new_houses_chart: flatlib Chart Object using which new house numbers have to be
                        computed, typically used along with KP Horary Method
        """
        PlanetsData = collections.namedtuple("PlanetsData",PLANETS_TABLE_COLS)

        # Get the house each planet is in
        planet_in_house = self.get_planet_in_house(planets_chart = chart, houses_chart = new_houses_chart) if new_houses_chart \
                        else self.get_planet_in_house(planets_chart = chart, houses_chart = chart)


        ascendant_data = self.get_ascendant_data(asc_data = chart.get(const.ASC), PlanetsDataCollection = PlanetsData)

        planets_data = []
        planets_data.append(ascendant_data)
        for planet in chart.objects:
            planet_obj = clean_select_objects_split_str(str(planet))
            planet_name, planet_lon_deg, planet_lat_deg = planet_obj[0], planet_obj[2], planet_obj[3]

            ## Get additional details like Nakshatra, RL, NL, SL details
            rl_nl_sl_data = self.get_rl_nl_sl_data(deg = planet.lon)
            planet_star = rl_nl_sl_data.get("Nakshatra", None)
            planet_rasi_lord = rl_nl_sl_data.get("RasiLord", None)
            planet_star_lord = rl_nl_sl_data.get("NakshatraLord", None)
            planet_sub_lord = rl_nl_sl_data.get("SubLord", None)
            planet_ss_lord = rl_nl_sl_data.get("SubSubLord", None)

            # Get the house the planet is in
            planet_house = planet_in_house.get(planet_name, None)

            ## Append data to NamedTuple Collection
            planets_data.append(PlanetsData(planet_name, planet.sign, planet.isRetrograde(), round(planet.lon,3),
                                            planet_lon_deg, round(planet.signlon, 3), planet_lat_deg, planet_star,
                                            planet_rasi_lord, planet_star_lord, planet_sub_lord, planet_ss_lord, planet_house))
        return planets_data

    def get_houses_data_from_chart(self, chart: Chart):
        """Generate the houses data table given a `flatlib.Chart` object"""
        HousesData = collections.namedtuple("HousesData", HOUSES_TABLE_COLS) # Create NamedTuple Collection to store data
        houses_data = []
        for house in chart.houses:
            house_obj = str(house).strip('<').strip('>').split()
            house_name, house_lon_deg, house_size = house_obj[0], house_obj[2], round(float(house_obj[3]), 3)
            house_nr = int(house_name.strip("House"))
            house_roman_nr = ROMAN_HOUSE_NUMBERS.get(house_name)

            ## Get additional details like Nakshatra, RL, NL, SL details
            rl_nl_sl_data = self.get_rl_nl_sl_data(deg = house.lon)
            house_star = rl_nl_sl_data.get("Nakshatra", None)
            house_star_lord = rl_nl_sl_data.get("NakshatraLord", None)
            house_rasi_lord = rl_nl_sl_data.get("RasiLord", None)
            house_sub_lord = rl_nl_sl_data.get("SubLord", None)
            house_ss_lord = rl_nl_sl_data.get("SubSubLord", None)


            ## Append data to NamedTuple Collection
            houses_data.append(HousesData(house_roman_nr, house_nr, house.sign, round(house.lon,3), house_lon_deg, round(house.signlon, 3),
                            house_size, house_star, house_rasi_lord, house_star_lord, house_sub_lord, house_ss_lord))
        return houses_data

    def get_consolidated_chart_data(self, planets_data: collections.namedtuple, houses_data: collections.namedtuple,
                                    return_style : str = None):
        """
        Create consolidated dict data where all objects (both planets and houses) are listed by rasi (sign).
        If `return_style == "dataframe_records"`, returns the consolidated data in the form of a list of dictionaries
        If `return_style == None`, returns the consolidated data in the form of a dictionary grouped by rasi
        """
        # Construct polars DataFrame of planets and houses data from the flatlib_sidereal Chart object
        req_cols = ["Rasi","Object","isRetroGrade", "LonDecDeg" ,"SignLonDMS", "SignLonDecDeg"]
        planets_df = pl.DataFrame(planets_data).select(req_cols)
        houses_df = pl.DataFrame(houses_data).with_columns(pl.lit(False).alias("isRetroGrade")).select(req_cols)

        ## Create joined dataframe of planets and houses data
        df_concat = pl.concat([houses_df, planets_df])

        # Group by 'Rasi' and aggregate all columns into a list or first non-null value
        result_df = df_concat.group_by('Rasi').agg([
            pl.col('Object').map_elements(list, return_dtype=pl.Object).alias('Object'),
            pl.col('isRetroGrade').map_elements(list, return_dtype=pl.Object).alias('isRetroGrade'),
            pl.col('LonDecDeg').map_elements(list, return_dtype=pl.Object).alias('LonDecDeg'),
            pl.col('SignLonDMS').map_elements(list, return_dtype=pl.Object).alias('SignLonDMS'),
            pl.col('SignLonDecDeg').map_elements(list, return_dtype=pl.Object).alias('SignLonDecDeg'),
            # pl.col('LatDMS').map_elements(list, return_dtype=pl.Object).alias('LatDMS')
        ])

        ## Sort by Rashis Order from `Aries` to `Pisces` in Clockwise Order
        result_df = result_df.with_columns(pl.col('Rasi').map_elements(lambda rasi: RASHIS.index(rasi), return_dtype=pl.Int32).alias('RashiOrder'))
        result_df = result_df.sort('RashiOrder').drop('RashiOrder') ## Sort by RashiOrder and Drop the column


        if return_style == "dataframe_records":
            return result_df.to_dicts()
        else:
            return self.get_consolidated_chart_data_rasi_wise(df = result_df)

    def get_consolidated_chart_data_rasi_wise(self, df: pl.DataFrame):
        """Returns in dict format, the consolidated chart data stored in a polars DataFrame grouped by Rasi"""
        final_dict = {}
        columns = df.columns

        for row in df.iter_rows():
            rasi = row[columns.index('Rasi')]
            final_dict[rasi] = {}
            for obj, is_retrograde, lon_dd, lon_dms, sign_lon_dd in zip(row[columns.index('Object')],
                                                                        row[columns.index('isRetroGrade')] ,
                                                                        row[columns.index('LonDecDeg')] ,
                                                                        row[columns.index('SignLonDMS')] ,
                                                                        row[columns.index('SignLonDecDeg')] ):

                final_dict[rasi][obj] = {"is_Retrograde": is_retrograde, "LonDecDeg": lon_dd,
                                        "SignLonDMS" : lon_dms, "SignLonDecDeg": sign_lon_dd}
        return final_dict


    def get_planet_in_house(self, houses_chart: Chart, planets_chart: Chart):
        """Determine which house each planet is in given a `flatlib.Chart` object"""
        planet_in_house = {}

        # Get the list of cusps (the boundary between two houses) along with their house numbers
        cusps = sorted([(house.lon, int(house.id.replace('House', ''))) for house in houses_chart.houses])
        # Add the first cusp (plus 360 degrees) as the end of the last house
        cusps.append((cusps[0][0] + 360, cusps[0][1]))
        # print("Cusps ADJ:",cusps)

        for planet in planets_chart.objects:
            planet_name = clean_select_objects_split_str(str(planet))[0]
            planet_lon = planet.lon
            for i in range(12):
                if cusps[i][0] <= planet_lon < cusps[i+1][0]:
                    planet_in_house[planet_name] = cusps[i][1]
                    break
                    ## Check if planet is overlapping into the last cusp
                elif cusps[i][0] <= planet_lon + 360 < cusps[i+1][0]:
                    planet_in_house[planet_name] = cusps[i][1]
                    break

        return planet_in_house

    def get_unique_house_nrs_for_rasi_lord(self, planets_df : pl.DataFrame, planet_name: str):
        """Returns the unique set of house numbers where the given planet is the rasi lord"""
        # Group by RasiLord and aggregate HouseNr into a list
        grouped_df = planets_df.group_by("RasiLord").agg([pl.col('HouseNr')\
                                .map_elements(list, return_dtype=pl.Object).alias('HouseNr')])

        # Filter the DataFrame for the given planet
        filtered_df = grouped_df.filter(pl.col('RasiLord') == planet_name)

        # If there are no matching rows, return an empty list
        if filtered_df.shape[0] == 0:
            return []

        # Get the list of house numbers for the given planet
        house_nrs = filtered_df['HouseNr'].to_list()[0]

        # Remove duplicates by converting the list to a set and then back to a list
        unique_house_nrs = list(set(house_nrs))

        return unique_house_nrs

    def get_planet_wise_significators(self, planets_data: collections.namedtuple, houses_data: collections.namedtuple):
        """Generate the ABCD significators table for each planet"""
        significators_table_cols = ["Planet", "A", "B", "C", "D"]
        SignificatorsData = collections.namedtuple("PlanetSignificators", significators_table_cols)

        # Get the planets data and Filter planets_data to remove objects like "Asc", "Chiron", "Syzygy", "Fortuna"
        planets_data = [planet for planet in planets_data if planet.Object not in ["Asc", "Chiron", "Syzygy", "Fortuna"]]

        # Get the house each planet is in
        planets_house_deposition = {data.Object: data.HouseNr for data in planets_data}


        significators_data = []
        for planet in planets_data:
            # A. House occupied by the star lord (Nakshatra Lord) of the planet
            A = planets_house_deposition.get(planet.NakshatraLord, None)

            # B. House occupied by the planet itself
            B = planet.HouseNr

            # C. House nrs where the star lord planet is also the rashi lord
            C = [data.HouseNr for data in houses_data if data.RasiLord == planet.NakshatraLord]

            # D. House nrs where the planet itself is also the rashi lord
            D = [data.HouseNr for data in houses_data if data.RasiLord == planet.Object]

            # Append data to NamedTuple Collection
            significators_data.append(SignificatorsData(planet.Object, A, B, C, D))

        return significators_data

    def get_house_wise_significators(self, planets_data : collections.namedtuple, houses_data: collections.namedtuple):
        """Generate the ABCD significators table for each house"""
        significators_table_cols = ["House", "A", "B", "C", "D"]
        SignificatorsData = collections.namedtuple("HouseSignificators", significators_table_cols)

        # Get the planets data and Filter planets_data to remove objects like "Asc", "Chiron", "Syzygy", "Fortuna"
        planets_data = [planet for planet in planets_data if planet.Object not in ["Asc", "Chiron", "Syzygy", "Fortuna"]]

        # Create a mapping of planets to their star lords (Nakshatra Lords)
        planet_to_star_lord = {data.Object: data.NakshatraLord for data in planets_data}

        significators_data = []
        for house in houses_data:
            # A. Planets in the star of occupants of that house
            # A1.1) Get all the rows which match with the house.HouseNr
            occupant_house_planets = [planet.Object for planet in planets_data if planet.HouseNr == house.HouseNr]
            # A1.2.) For each planet in occupant_house_planets find out if that planet is the Nakshatra Lord for any row in the planets_data
            A = [planet.Object for planet in planets_data if planet.NakshatraLord in occupant_house_planets]

            # B. Planets in that house
            B = [planet.Object for planet in planets_data if planet.HouseNr == house.HouseNr]

            # C. Planets in the star of owners of that house
            C = [planet for planet, star_lord in planet_to_star_lord.items() if star_lord == house.RasiLord]

            # D. Owner of that house
            D = house.RasiLord

            # Append data to NamedTuple Collection
            significators_data.append(SignificatorsData(house.Object, A, B, C, D))

        return significators_data


    def compute_vimshottari_dasa(self, chart: Chart):
        """
        Computes the Vimshottari Dasa for the chart including Maha Dasha, Bhukti, and Pratyantar.
        Returns sorted output with earlier dates on top.
        """
        # Get the moon object from the chart
        moon = chart.get(const.MOON)
        moon_details = clean_select_objects_split_str(str(moon))

        # Moon's Details
        moon_rl_nl_sl = self.get_rl_nl_sl_data(deg = moon.lon)
        moon_nakshatra = moon_rl_nl_sl["Nakshatra"]
        moon_nakshatra_lord = moon_rl_nl_sl["NakshatraLord"]
        moon_sign_lord = moon_rl_nl_sl["RasiLord"]

        # Helper function to format datetime objects to string
        dt_tuple_str = lambda start_date: start_date.strftime("%d-%m-%Y")

        # Define the sequence of the Dasa periods and their lengths
        dasa_sequence = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
        dasa_lengths = [7, 20, 6, 10, 7, 18, 16, 19, 17]
        dasa_years = dict(zip(dasa_sequence, dasa_lengths))

        # Find the starting point of the Dasa sequence
        start_index = dasa_sequence.index(moon_nakshatra_lord)

        # Reorder the Dasa sequence to start with the moon's Nakshatra Lord
        dasa_sequence = dasa_sequence[start_index:] + dasa_sequence[:start_index]
        dasa_lengths = dasa_lengths[start_index:] + dasa_lengths[:start_index]
        dasa_order = dict(zip(dasa_sequence, dasa_lengths))

        # Calculate initial dates and periods
        typical_nakshatra_arc = 800
        nakshatra_start = NAKSHATRAS.index(moon_nakshatra) * typical_nakshatra_arc
        moon_lon_mins = round(moon.lon * 60, 2)
        elapsed_moon_mins = moon_lon_mins - nakshatra_start
        remaining_arc_mins = typical_nakshatra_arc - elapsed_moon_mins
        starting_dasa_duration = dasa_order[moon_nakshatra_lord]
        start_dasa_remaining_duration = (starting_dasa_duration/typical_nakshatra_arc) * remaining_arc_mins
        start_dasa_elapsed_duration = starting_dasa_duration - start_dasa_remaining_duration

        chart_date = (self.year, self.month, self.day, self.hour, self.minute)
        dasa_start_date = compute_new_date(start_date=chart_date, diff_value=start_dasa_elapsed_duration, direction="backward")

        def calculate_pratyantar_periods(maha_planet, bhukti_planet, bhukti_start_date):
            """Calculate Pratyantar periods for a given Bhukti"""
            if isinstance(bhukti_start_date, str):
                bhukti_start_date = datetime.strptime(bhukti_start_date, '%d-%m-%Y')

            maha_years = dasa_years[maha_planet]
            bhukti_duration = (dasa_years[bhukti_planet] * maha_years) / 120

            pratyantar_periods = {}
            current_date = bhukti_start_date

            # Start Pratyantar sequence from the Bhukti planet
            bhukti_index = dasa_sequence.index(bhukti_planet)
            pratyantar_sequence = dasa_sequence[bhukti_index:] + dasa_sequence[:bhukti_index]

            for pratyantar_planet in pratyantar_sequence:
                # Calculate Pratyantar duration
                pratyantar_duration = (dasa_years[pratyantar_planet] * bhukti_duration) / 120
                end_date = current_date + timedelta(days=int(pratyantar_duration * 365.25))

                pratyantar_periods[pratyantar_planet] = {
                    'start': current_date.strftime('%d-%m-%Y'),
                    'end': end_date.strftime('%d-%m-%Y')
                }

                current_date = end_date

            return pratyantar_periods

        # Store all dasha periods
        dasha_periods = []

        # Calculate all periods
        for i in range(len(dasa_sequence)):
            dasa = dasa_sequence[i]
            dasa_length = dasa_lengths[i]
            dasa_end_date = compute_new_date(start_date=tuple(dasa_start_date.timetuple())[:5],
                                           diff_value=dasa_length, direction="forward")

            bhukti_periods = {}
            bhukti_start_date = dasa_start_date

            # Calculate Bhukti periods
            bhukti_start_index = dasa_sequence.index(dasa)
            bhukti_sequence = dasa_sequence[bhukti_start_index:] + dasa_sequence[:bhukti_index]

            for bhukti in bhukti_sequence:
                bhukti_length = dasa_length * dasa_years[bhukti] / 120
                bhukti_end_date = compute_new_date(start_date=tuple(bhukti_start_date.timetuple())[:5],
                                                 diff_value=bhukti_length, direction="forward")

                # Calculate Pratyantar periods for this Bhukti
                pratyantar_periods = calculate_pratyantar_periods(dasa, bhukti, bhukti_start_date)
                print(pratyantar_periods)
                bhukti_periods[bhukti] = {
                    'start': dt_tuple_str(bhukti_start_date),
                    'end': dt_tuple_str(bhukti_end_date),
                    'pratyantars': pratyantar_periods
                }

                bhukti_start_date = bhukti_end_date

            dasha_periods.append({
                'planet': dasa,
                'start': dasa_start_date,
                'end': dasa_end_date,
                'bhuktis': bhukti_periods
            })

            dasa_start_date = dasa_end_date

        # Create final dictionary
        vimshottari_dasa = {
            d['planet']: {
                'start': dt_tuple_str(d['start']),
                'end': dt_tuple_str(d['end']),
                'bhuktis': {
                    bhukti: {
                        'start': bhukti_data['start'],
                        'end': bhukti_data['end'],
                        'pratyantars': bhukti_data['pratyantars']
                    }
                    for bhukti, bhukti_data in d['bhuktis'].items()
                }
            }
            for d in dasha_periods
        }

        return vimshottari_dasa
