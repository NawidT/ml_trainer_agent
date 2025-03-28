
import pandas as pd
import pickle

# Create a list of house prices and corresponding areas in Qatar
house_prices_data = {
    'Area': ['Doha', 'Al Rayyan', 'Lusail', 'West Bay', 'The Pearl-Qatar', 'Al Wakrah', 'Al Khor', 'Mushereib', 
             'Al Sadd', 'Education City', 'Barwa City', 'Villaggio', 'Al Duhail', 'Qatar University', 
             'Hilal', 'Al Gharaffa', 'Salwa', 'Al Mashaf', 'Qatar Sports Club', 'Al Hilal'],
    'Price (QAR)': [3500000, 2500000, 5000000, 4200000, 6000000, 1800000, 2200000, 1400000, 
                     2000000, 2300000, 3600000, 2800000, 1800000, 1700000, 1500000, 3000000, 
                     1900000, 2200000, 2100000, 2800000]  # Correct lengths to match
}

# Creating the DataFrame
house_prices_df = pd.DataFrame(house_prices_data)
print("House Prices DataFrame created successfully.")
print(house_prices_df)

# Identify the area with the highest house prices
highest_price_area = house_prices_df.loc[house_prices_df['Price (QAR)'].idxmax()]
print("\nArea with the highest house prices:")
print(highest_price_area)

# Store results in memory
memory_dict = {}
memory_dict['house_prices_df'] = house_prices_df
memory_dict['highest_price_area'] = highest_price_area
pickle.dump(memory_dict, open('tmp/memory.pkl', 'wb'))
print("\nData stored in memory successfully.")
