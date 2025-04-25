# Vedic Astrological Yogas Reference

This document provides detailed information about the various yogas (planetary combinations) implemented in the VedicAstro system.

## Introduction to Yogas

In Vedic astrology, yogas are specific combinations or arrangements of planets that indicate particular effects in a person's life. These planetary combinations can have profound impacts on an individual's character, behavior, and life circumstances.

This document categorizes yogas based on their general effects:

## Benefic Yogas (Auspicious Combinations)

### Raj Yogas (Royal Combinations)

| Yoga Name                | Formation                                                                          | Effects                                           |
| ------------------------ | ---------------------------------------------------------------------------------- | ------------------------------------------------- |
| Raj Yoga                 | Connections between Kendra (1st, 4th, 7th, 10th) and Trikona (1st, 5th, 9th) lords | Power, status, success, and royal influence       |
| Gaja-Kesari Yoga         | Jupiter in a quadrant from Moon                                                    | Leadership qualities, fame, success, intelligence |
| Budha-Aditya Yoga        | Sun and Mercury together                                                           | Intelligence, communication skills, leadership    |
| Amala Yoga               | Benefic in 10th from Moon or Lagna                                                 | Good reputation, fame, clean character            |
| Dharma-Karmadhipati Yoga | Lords of 9th and 10th houses conjunct or 9th lord in 10th                          | Power, deep success in career and duty            |
| Parvata Yoga             | Benefics in kendras and no malefics in kendras                                     | Fame, reputation, and prosperity                  |
| Kahala Yoga              | 4th and 9th lords strong/in kendra/trikona                                         | Courage, leadership, success                      |

### Dhana Yogas (Wealth Combinations)

| Yoga Name           | Formation                                                | Effects                                   |
| ------------------- | -------------------------------------------------------- | ----------------------------------------- |
| Dhana Yoga          | Lords of 2nd and 11th houses conjunct                    | Financial prosperity, wealth acquisition  |
| Lakshmi Yoga        | 9th lord strong in own/exalted sign and related to Lagna | Wealth, luxury, grace, good fortune       |
| Chandra-Mangal Yoga | Moon + Mars conjunction or mutual aspect                 | Wealth and business success               |
| Saraswati Yoga      | Jupiter, Venus, and Mercury in angles/trines             | Wisdom, education, wealth, and creativity |

### Pancha Mahapurusha Yogas (Five Great Person Yogas)

| Yoga Name    | Formation                                 | Effects                                              |
| ------------ | ----------------------------------------- | ---------------------------------------------------- |
| Ruchaka Yoga | Mars in own/exalted sign in a quadrant    | Military prowess, courage, leadership                |
| Bhadra Yoga  | Mercury in own/exalted sign in a quadrant | Intelligence, business acumen, communication         |
| Hamsa Yoga   | Jupiter in own/exalted sign in a quadrant | Wisdom, spirituality, good fortune                   |
| Malavya Yoga | Venus in own/exalted sign in a quadrant   | Beauty, artistic talent, luxury, relationship skills |
| Sasa Yoga    | Saturn in own/exalted sign in a quadrant  | Discipline, longevity, professional success          |

### Other Benefic Yogas

| Yoga Name              | Formation                                        | Effects                                             |
| ---------------------- | ------------------------------------------------ | --------------------------------------------------- |
| Adhi Yoga              | Benefics in 6th, 7th, 8th from Moon              | Strong leadership, governmental power               |
| Neech Bhanga Raja Yoga | Debilitated planet getting cancellation          | Turns weakness into strength                        |
| Parivartana Yoga       | Exchange of signs between planets                | Mutual strength in both houses involved             |
| Maha Bhagya Yoga       | Jupiter in Lagna with Moon in 7th or 9th         | Extraordinary fortune and success                   |
| Shankha Yoga           | Lords of 5th and 6th houses conjunct in kendra   | Wisdom, diplomacy, spiritual inclination            |
| Jnana Yoga             | Jupiter or Mercury in 1st, 4th, 5th or 9th house | Wisdom, spiritual knowledge, intellectual abilities |

## Intellectual & Spiritual Yogas

| Yoga Name         | Formation                                                       | Effects                                             |
| ----------------- | --------------------------------------------------------------- | --------------------------------------------------- |
| Saraswati Yoga    | Jupiter, Venus, and Mercury in angles/trines                    | Wisdom, education, artistic abilities               |
| Budha-Aditya Yoga | Sun and Mercury in same sign                                    | Intelligence, communication, administrative skills  |
| Jnana Yoga        | Jupiter or Mercury in 1st, 4th, 5th, or 9th house               | Wisdom, spiritual knowledge, intellectual abilities |
| Brahma Yoga       | Jupiter and Mercury connected with 5th/9th house or lords       | Spiritual wisdom, philosophical knowledge           |
| Vidya Yoga        | Strong 2nd, 4th, 5th lords                                      | Education, learning abilities                       |
| Shankha Yoga      | Lords of 5th and 6th houses conjunct in kendra or in opposition | Wisdom, diplomacy, ethics, spiritual inclination    |

## Nabhasa Yogas (Special Planetary Patterns)

| Yoga Name  | Formation                                    | Effects                                        |
| ---------- | -------------------------------------------- | ---------------------------------------------- |
| Yuga Yoga  | All classical planets in 6 consecutive signs | Versatility, leadership, collaborative success |
| Rajju Yoga | 5+ planets in specific house patterns        | Various effects based on the specific pattern  |

## Malefic Yogas (Challenging Combinations)

| Yoga Name       | Formation                                     | Effects                                          |
| --------------- | --------------------------------------------- | ------------------------------------------------ |
| Grahan Yoga     | Sun/Moon with Rahu/Ketu                       | Karmic disturbance, eclipse-like effects         |
| Kemadruma Yoga  | Moon with no planets adjacent or aspecting    | Loneliness, instability, hardships               |
| Shakata Yoga    | Moon and Jupiter in 6/8 position              | Emotional ups and downs, challenges              |
| Daridra Yoga    | 5th and 9th lords in 6th, 8th, or 12th houses | Financial struggles, poverty                     |
| Pitra Dosha     | Sun afflicted by malefics                     | Ancestral karmic issues, father-related problems |
| Kaal Sarp Dosha | All planets between Rahu and Ketu             | Intense karma, struggle, or transformation       |

## Positive Transformations of "Negative" Yogas

| Yoga Name          | Formation                            | Effects                                                  |
| ------------------ | ------------------------------------ | -------------------------------------------------------- |
| Viparita Raja Yoga | Malefics in 6th, 8th, or 12th houses | Success through hardship, turning negative into positive |

## How Yogas Are Calculated

In the VedicAstro system, yogas are calculated by examining:

1. **Planetary positions** - The houses and signs occupied by planets in the sidereal zodiac
2. **House lordships** - Which planet rules which house
3. **Aspects** - Which planets are aspecting each other
4. **Special relationships** - Exaltation, debilitation, own house, etc.

> **Important Note**: Yoga calculations in VedicAstro use the rasi chart data based on the sidereal zodiac positions (using Lahiri ayanamsa). This ensures that yoga determinations are in accordance with traditional Vedic astrology principles.

Multiple yogas can exist simultaneously in a birth chart, and their effects can compound or modify each other.

## Using Yoga Analysis in Interpretation

When interpreting the presence of yogas in a chart:

1. **Consider strength** - Not all yogas manifest with the same strength
2. **Check for cancellation** - Some yogas may be cancelled by other factors
3. **Examine house activation** - Yogas become more prominent when activated by transits or dashas
4. **Look at the whole chart** - Individual yogas should be interpreted in the context of the entire chart

## API Usage

To get yoga analysis through the API:

```python
import requests

# Set up birth data
birth_data = {
    "year": 1990,
    "month": 6,
    "day": 15,
    "hour": 12,
    "minute": 30,
    "second": 0,
    "utc": "5.5",  # UTC offset
    "latitude": 28.6139,  # New Delhi
    "longitude": 77.2090,
    "ayanamsa": "Lahiri",
    "house_system": "Placidus"
}

# Standard categorization (by yoga type)
response = requests.post("http://localhost:8088/get_yogas", json=birth_data)
yoga_results = response.json()

# Display results
for category, yogas in yoga_results.items():
    print(f"\n--- {category} ---")
    for yoga in yogas:
        print(f"{yoga['name']}: {yoga['description']}")

# Alternative: Categorize by influence (benefic/malefic)
response = requests.post("http://localhost:8088/get_yogas?categorize_by_influence=true", json=birth_data)
influence_results = response.json()

# Display benefic and malefic yogas
print("\n--- BENEFIC YOGAS ---")
for yoga in influence_results["benefic_yogas"]:
    print(f"{yoga['name']}: {yoga['description']}")

print("\n--- MALEFIC YOGAS ---")
for yoga in influence_results["malefic_yogas"]:
    print(f"{yoga['name']}: {yoga['description']}")
```

### API Parameters

The `/get_yogas` endpoint accepts the following parameters:

| Parameter                 | Type                  | Description                                                                                                  |
| ------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| `horo_input`              | JSON object           | Birth chart data including date, time, location, and calculation settings                                    |
| `categorize_by_influence` | Boolean (query param) | If `true`, yogas are categorized as benefic or malefic rather than by traditional types. Default is `false`. |

### Example Testing

You can test the yogas functionality from the command line:

```bash
# Standard categorization (by yoga type)
python test_extended_yogas.py

# Categorize by influence (benefic/malefic)
python test_extended_yogas.py --by-influence
```

### Other Special Yogas

| Yoga Name           | Formation                                        | Effects                        |
| ------------------- | ------------------------------------------------ | ------------------------------ |
| Vesi Yoga           | Planet in 2nd from Sun                           | Power of speech and persuasion |
| Shubha Vesi Yoga    | Benefic in 2nd from Sun                          | Auspicious speech, eloquence   |
| Ubhayachari Yoga    | Planets in both 2nd and 12th from Sun            | Balanced speech and thought    |
| Trikona-Kendra Yoga | Trikona lord in kendra or kendra lord in trikona | Authority, success, leadership |
