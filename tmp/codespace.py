
import pandas as pd
import numpy as np
import pickle

# Load previous memory or initialize a new dictionary
tmp_dict = {}
try:
    tmp_dict = pickle.load(open('tmp/memory.pkl', 'rb'))
except FileNotFoundError:
    print("Memory file not found. Initializing a new memory.")

# Generate a list of 20 random house prices in Qatar
np.random.seed(42)  # For reproducibility
house_prices = np.random.randint(200000, 1000000, size=20)
areas = ['Doha', 'Al Wakrah', 'Lusail', 'Al Rayyan', 'Madinat ash Shamal', 
         'Umm Salal', 'Al Khor', 'Dukhan', 'Al Dhakira', 'Umm Salal Ali', 
         'Wakif', 'Al Gharrafa', 'Mushayrib', 'The Pearl', 'West Bay', 
         'Corniche', 'Al Sadd', 'Salwa', 'Qatar University', 'Al Muraikh']

# Create a DataFrame for better handling
df = pd.DataFrame({
    'Area': areas[:20],
    'Price': house_prices
})

# Find the area with the highest house price
highest_price_row = df.loc[df['Price'].idxmax()]
highest_price_area = highest_price_row['Area']
highest_price_value = highest_price_row['Price']

# Print the results
print("Generated House Prices in Qatar:")
print(df)
print(f"The area with the highest house price is {highest_price_area} with a price of {highest_price_value}.")

# Store the results in memory
tmp_dict['house_prices'] = df.to_dict(orient='records')
pickle.dump(tmp_dict, open('tmp/memory.pkl', 'wb'))
