"""
Configuration for the Omakase rating pipeline.
Copy this file to config.py and fill in your API key.
"""

# Google Places API key — get one at https://console.cloud.google.com/
GOOGLE_API_KEY = "YOUR_API_KEY_HERE"

# Restaurants you've personally visited (for highlighting in charts)
VISITED = [
    "Shinn East",
    "One Bite Omakase",
    "SourAji",
    "Shiki Omakase",
]

# Scoring parameters
RATING_METHOD = "wilson"
WILSON_Z = 1.96
GOOGLE_BIAS_CORRECTION = 0.97
PRICE_EXPONENT = "auto"

# Exclusion keywords (restaurants matching these are filtered out)
EXCLUDE_KEYWORDS = ["closed", "excluded"]
