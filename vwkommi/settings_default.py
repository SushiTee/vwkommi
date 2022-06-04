"""Module containing the default settings."""
import os

# Base path for module
BASE_DIR = os.path.dirname(__file__)

# VW user data (make sure to change it to correct data)
VW_USERNAME = 'example_user'
VW_PASSWORD = 'example_password'

# known request prefixes
PREFIX_LIST = [185, 900, 877, 902] # known prefixes for ID.3/4/5

# commission number range
COMMISSION_NUMBER_RANGE = [
    ('AF', 5000, 9999),
    ('AG', 0, 9999),
    ('AH', 0, 9999),
    ('AI', 0, 9999),
    ('AJ', 0, 9999),
    ('AK', 0, 9999),
    ('AL', 0, 9999),
]
