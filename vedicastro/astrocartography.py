from typing import List, Dict, Any, Tuple
import math
import collections
# import numpy as np
from flatlib import const

# Constants for Earth measurements
EARTH_RADIUS_KM = 6371.0

# Types of lines to calculate
LINE_TYPES = {
    "Ascendant": {"abbreviation": "AS", "color": "#FF0000"},  # Red
    "Midheaven": {"abbreviation": "MC", "color": "#0000FF"},  # Blue
    "Descendant": {"abbreviation": "DS", "color": "#FF8800"},  # Orange
    "Imum Coeli": {"abbreviation": "IC", "color": "#00FF00"},  # Green
    "Conjunct": {"abbreviation": "Co", "color": "#800080"},   # Purple
    "Opposition": {"abbreviation": "Op", "color": "#808080"}, # Gray
}

class AstrocartographyCalculator:
    """Calculates astrocartography lines for a given chart"""

    def __init__(self, vedic_chart_data):
        """
        Initialize with a VedicHoroscopeData object

        Parameters:
        -----------
        vedic_chart_data: VedicHoroscopeData
            The chart data to use for astrocartography calculations
        """
        self.chart_data = vedic_chart_data
        self.chart = vedic_chart_data.generate_chart()
        self.base_longitude = vedic_chart_data.longitude
        self.base_latitude = vedic_chart_data.latitude

    def calculate_angle_planet_to_line(self, planet_lon: float, line_type: str) -> float:
        """
        Calculate the longitude where a planet forms a specific angular relationship
        with one of the four angles (Asc, MC, Desc, IC)

        Parameters:
        -----------
        planet_lon: float
            The longitude of the planet in degrees
        line_type: str
            The type of line to calculate (Ascendant, Midheaven, Descendant, Imum Coeli)

        Returns:
        --------
        float: The longitude where the planet forms the specified relationship
        """
        if line_type == "Ascendant":
            # Ascendant line: planet is rising on the eastern horizon
            return (planet_lon - 90) % 360
        elif line_type == "Midheaven":
            # Midheaven line: planet is at the highest point in the sky
            return planet_lon
        elif line_type == "Descendant":
            # Descendant line: planet is setting on the western horizon
            return (planet_lon + 90) % 360
        elif line_type == "Imum Coeli":
            # IC line: planet is at the lowest point in the sky
            return (planet_lon + 180) % 360
        else:
            raise ValueError(f"Unsupported line type: {line_type}")

    def calculate_planet_lines(self, planet_id: str, resolution: int = 180) -> Dict[str, List[Tuple[float, float]]]:
        """
        Calculate all astrocartography lines for a specific planet

        Parameters:
        -----------
        planet_id: str
            The ID of the planet to calculate lines for (e.g., 'Sun', 'Moon', etc.)
        resolution: int
            The number of latitude points to calculate for each line

        Returns:
        --------
        Dict[str, List[Tuple[float, float]]]: Dictionary mapping line types to lists of coordinates
        """
        planet = self.chart.get(planet_id)
        planet_lon = planet.lon

        lines = {}

        # Calculate latitudes from -90 to +90 degrees
        # Using standard Python instead of numpy
        step = 180.0 / (resolution - 1) if resolution > 1 else 180.0
        latitudes = [-90.0 + i * step for i in range(resolution)]

        for line_type in ["Ascendant", "Midheaven", "Descendant", "Imum Coeli"]:
            base_longitude = self.calculate_angle_planet_to_line(planet_lon, line_type)

            # For each latitude, calculate the corresponding longitude
            coordinates = []
            for lat in latitudes:
                # Adjust for Earth's curvature - this is a simplified model
                # More accurate models might be needed for professional applications
                if line_type in ["Ascendant", "Descendant"]:
                    # These lines curve more at extreme latitudes
                    adjustment = 0
                    if abs(lat) > 60:
                        # Simplified adjustment factor, more complex in reality
                        adjustment = (abs(lat) - 60) * 3

                    if line_type == "Ascendant":
                        lon = (base_longitude + adjustment) % 360
                    else:  # Descendant
                        lon = (base_longitude - adjustment) % 360
                else:
                    # Midheaven and IC are relatively straight lines of longitude
                    lon = base_longitude

                coordinates.append((lat, lon))

            lines[line_type] = coordinates

        return lines

    def calculate_all_planet_lines(self, planets: List[str] = None) -> Dict[str, Dict[str, List[Tuple[float, float]]]]:
        """
        Calculate all astrocartography lines for all specified planets

        Parameters:
        -----------
        planets: List[str], optional
            List of planet IDs to calculate lines for. If None, uses all major planets.

        Returns:
        --------
        Dict[str, Dict[str, List[Tuple[float, float]]]]: Nested dictionary mapping planets and line types to coordinates
        """
        if planets is None:
            planets = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
                       const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO]

        all_lines = {}

        for planet_id in planets:
            all_lines[planet_id] = self.calculate_planet_lines(planet_id)

        return all_lines

    def format_astrocartography_data(self, all_lines: Dict[str, Dict[str, List[Tuple[float, float]]]]) -> List[Dict[str, Any]]:
        """
        Format astrocartography line data for API response

        Parameters:
        -----------
        all_lines: Dict[str, Dict[str, List[Tuple[float, float]]]]
            The output from calculate_all_planet_lines()

        Returns:
        --------
        List[Dict[str, Any]]: List of line data entries for API response
        """
        formatted_data = []

        for planet_id, planet_lines in all_lines.items():
            planet_obj = self.chart.get(planet_id)

            # Get planet name, potentially cleaning up or formatting
            planet_name = planet_id.replace("North Node", "Rahu").replace("South Node", "Ketu")

            # Is the planet retrograde?
            is_retrograde = planet_obj.isRetrograde()

            for line_type, coordinates in planet_lines.items():
                # Format coordinates as [lat, lon] pairs for mapping libraries
                formatted_coordinates = [[lat, lon] for lat, lon in coordinates]

                # Create line entry
                line_entry = {
                    "planet": planet_name,
                    "lineType": line_type,
                    "abbreviation": LINE_TYPES[line_type]["abbreviation"],
                    "color": LINE_TYPES[line_type]["color"],
                    "isRetrograde": is_retrograde,
                    "coordinates": formatted_coordinates
                }

                formatted_data.append(line_entry)

        return formatted_data

    def get_astrocartography_data(self, planets: List[str] = None) -> Dict[str, Any]:
        """
        Get complete astrocartography data for specified planets

        Parameters:
        -----------
        planets: List[str], optional
            List of planet IDs to include. If None, uses all major planets.

        Returns:
        --------
        Dict[str, Any]: Complete astrocartography data for API response
        """
        all_lines = self.calculate_all_planet_lines(planets)
        formatted_data = self.format_astrocartography_data(all_lines)

        # Add metadata for the response
        result = {
            "status": "success",
            "birthLocation": {
                "latitude": self.base_latitude,
                "longitude": self.base_longitude
            },
            "lines": formatted_data
        }

        return result
