"""
Test script to verify property matching logic works correctly
"""
import sys
sys.path.insert(0, '/Users/nischalgurung/Desktop/Seo-optima v3')

from dashboard.services.keyword_extractor import _property_matches_domain, _generate_url_variations

# Test data from your account
properties = [
    "sc-domain:homeschool.asia",
    "https://www.kungfuquiz.com/",
    "sc-domain:ciepastpapers.com",
    "https://homeschool.asia/"
]

# Test cases
test_urls = [
    "https://www.ciepastpapers.com/",
    "ciepastpapers.com",
    "https://homeschool.asia/",
    "https://www.kungfuquiz.com/",
    "kungfuquiz.com"
]

print("="*80)
print("PROPERTY MATCHING TEST")
print("="*80)

for user_input in test_urls:
    print(f"\n📝 User Input: {user_input}")
    print("-" * 80)
    
    variations = _generate_url_variations(user_input, properties)
    print(f"Generated {len(variations)} variations:")
    for i, v in enumerate(variations[:5], 1):
        print(f"  {i}. {v}")
    if len(variations) > 5:
        print(f"  ... and {len(variations) - 5} more")
    
    print("\n✅ First 3 attempts will be:")
    for i, v in enumerate(variations[:3], 1):
        print(f"  {i}. {v}")
