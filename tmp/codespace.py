
import pandas as pd
import random

# Generate a list of house prices in different areas of Qatar
areas = ['Doha', 'Lusail', 'Al Rayyan', 'Katara', 'West Bay', 'The Pearl-Qatar', 'Mushayrib', 'Al Wakrah', 'Al Khor', 'Al Daayen', 'Al Thumama', 'Shehaniya', 'Umm Salal', 'Al Gharafa', 'Al Hilal', 'Al Sadd', 'Onaiza', 'Al Jazeera', 'Al Markhiya', 'Al Duhail']
house_prices = {area: random.randint(50000, 2000000) for area in areas}
house_prices_df = pd.DataFrame(house_prices.items(), columns=['Area', 'Price'])

# Convert prices to float
house_prices_df['Price'] = house_prices_df['Price'].astype(float)

# Print the generated dataframe
print("Generated House Prices DataFrame:")
print(house_prices_df)

# Find the area with the highest house price
highest_price_area = house_prices_df.loc[house_prices_df['Price'].idxmax()]
print("Area with the highest house price:")
print(highest_price_area)

house_prices_df, highest_price_area
