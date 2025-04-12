from vedicastro.VedicAstro import VedicHoroscopeData
from pprint import pprint
import json
from datetime import datetime, timedelta
from flatlib import const
from flatlib.chart import Chart

def compute_vimshottari_dasa(chart: Chart, birth_year, birth_month, birth_day, birth_hour, birth_minute):
    """
    Computes the Vimshottari Dasa for the chart including Maha Dasha, Bhukti, and Pratyantar.
    Returns sorted output with earlier dates on top.
    """
    # Get the moon object from the chart
    moon = chart.get(const.MOON)

    # Define constants
    NAKSHATRAS = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
        "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
        "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
        "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]

    # Helper function to format datetime objects to string
    dt_tuple_str = lambda start_date: start_date.strftime("%d-%m-%Y")

    # Define the sequence of the Dasa periods and their lengths
    dasa_sequence = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
    dasa_lengths = [7, 20, 6, 10, 7, 18, 16, 19, 17]
    dasa_years = dict(zip(dasa_sequence, dasa_lengths))

    # Get Moon's Nakshatra and Lord
    moon_lon = moon.lon
    nakshatra_index = int(moon_lon // 13.333333)
    moon_nakshatra = NAKSHATRAS[nakshatra_index]
    moon_nakshatra_lord = dasa_sequence[nakshatra_index % 9]

    # Find the starting point of the Dasa sequence
    start_index = dasa_sequence.index(moon_nakshatra_lord)

    # Reorder the Dasa sequence
    dasa_sequence = dasa_sequence[start_index:] + dasa_sequence[:start_index]
    dasa_lengths = dasa_lengths[start_index:] + dasa_lengths[:start_index]
    dasa_order = dict(zip(dasa_sequence, dasa_lengths))

    # Calculate initial dates and periods
    typical_nakshatra_arc = 800
    nakshatra_start = NAKSHATRAS.index(moon_nakshatra) * typical_nakshatra_arc
    moon_lon_mins = round(moon_lon * 60, 2)
    elapsed_moon_mins = moon_lon_mins - nakshatra_start
    remaining_arc_mins = typical_nakshatra_arc - elapsed_moon_mins
    starting_dasa_duration = dasa_order[moon_nakshatra_lord]
    start_dasa_remaining_duration = (starting_dasa_duration/typical_nakshatra_arc) * remaining_arc_mins
    start_dasa_elapsed_duration = starting_dasa_duration - start_dasa_remaining_duration

    # Calculate start date
    birth_date = datetime(birth_year, birth_month, birth_day, birth_hour, birth_minute)
    dasa_start_date = birth_date - timedelta(days=int(start_dasa_elapsed_duration * 365.25))

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
            pratyantar_duration = (dasa_years[pratyantar_planet] * bhukti_duration) / 120
            end_date = current_date + timedelta(days=int(pratyantar_duration * 365.25))

            pratyantar_periods[pratyantar_planet] = {
                'start': current_date.strftime('%d-%m-%Y'),
                'end': end_date.strftime('%d-%m-%Y')
            }

            current_date = end_date

        return pratyantar_periods

    # Calculate all periods
    dasha_periods = []
    current_dasa_start = dasa_start_date

    for i, dasa in enumerate(dasa_sequence):
        dasa_length = dasa_lengths[i]
        dasa_end_date = current_dasa_start + timedelta(days=int(dasa_length * 365.25))

        bhukti_periods = {}
        current_bhukti_start = current_dasa_start

        # Calculate Bhukti periods
        bhukti_start_index = dasa_sequence.index(dasa)
        bhukti_sequence = dasa_sequence[bhukti_start_index:] + dasa_sequence[:bhukti_start_index]

        for bhukti in bhukti_sequence:
            bhukti_length = dasa_length * dasa_years[bhukti] / 120
            bhukti_end_date = current_bhukti_start + timedelta(days=int(bhukti_length * 365.25))

            # Calculate Pratyantar periods
            pratyantar_periods = calculate_pratyantar_periods(dasa, bhukti, current_bhukti_start)

            bhukti_periods[bhukti] = {
                'start': dt_tuple_str(current_bhukti_start),
                'end': dt_tuple_str(bhukti_end_date),
                'pratyantars': pratyantar_periods
            }

            current_bhukti_start = bhukti_end_date

        dasha_periods.append({
            'planet': dasa,
            'start': current_dasa_start,
            'end': dasa_end_date,
            'bhuktis': bhukti_periods
        })

        current_dasa_start = dasa_end_date

    # Create final dictionary
    vimshottari_dasa = {
        d['planet']: {
            'start': dt_tuple_str(d['start']),
            'end': dt_tuple_str(d['end']),
            'antardashas': d['bhuktis']
        }
        for d in dasha_periods
    }

    return vimshottari_dasa

def compute_vimshottari_dasa_enahanced(year, month, day, hour, minute, second, latitude, longitude, utc, ayanamsa=None, house_system=None):

    if ayanamsa is None:
        ayanamsa = "Lahiri"
    if house_system is None:
        house_system = "Placidus"
    # Step 4: Create VedicHoroscopeData instance
    vhd = VedicHoroscopeData(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        second=second,
        tz=utc,
        latitude=latitude,
        longitude=longitude,
        ayanamsa=ayanamsa,
        house_system=house_system
    )

    # Step 5: Generate the birth chart
    chart = vhd.generate_chart()

    # Step 6: Compute Vimshottari Dasa
    vimshottari_dasa = compute_vimshottari_dasa(chart, year, month, day, hour, minute)
    # pprint(vimshottari_dasa)
    # Step 7: Save to JSON file with validation
    output_filename = f"vimshottari_dasa_{year}{month:02d}{day:02d}.json"

    # Create a data dictionary with birth details and dasha data
    data_to_save = {
        "birth_details": {
            "date": f"{year}-{month:02d}-{day:02d}",
            "time": f"{hour:02d}:{minute:02d}:{second:02d}",
            "latitude": latitude,
            "longitude": longitude,
            "utc": utc,
            "ayanamsa": ayanamsa,
            "house_system": house_system
        },
        "vimshottari_dasa": vimshottari_dasa
    }

    # Validate the data structure
    for maha_dasha, maha_data in vimshottari_dasa.items():
        for bhukti, bhukti_data in maha_data['antardashas'].items():
            if 'pratyantars' not in bhukti_data:
                # print(f"Warning: Pratyantars missing for {maha_dasha}-{bhukti}")
                bhukti_data['pratyantars'] = {}  # Add empty dict if missing

    # Save to JSON file
    # with open(output_filename, 'w', encoding='utf-8') as f:
    #     json.dump(data_to_save, f, indent=2, ensure_ascii=False)

    return vimshottari_dasa



