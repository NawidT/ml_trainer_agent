
import pandas as pd
import pickle

# Creating a sample dataframe to represent house prices in different areas of Qatar
area_names = ['Doha', 'Al Wakrah', 'Al Khor', 'Lusail', 'Umm Salal', 'Al Rayyan', 
              'Madinat ash Shamal', 'Al Daayen', 'Al Sheehaniya', 'Al Ghuwairiya', 
              'Qatar University', 'Al Wakif', 'The Pearl', 'West Bay', 'Mushreib', 
              'Salwa', 'Industrial Area', 'Al Hilal', 'Al Jazeera', 'Aspire']

house_prices = [1200000, 950000, 800000, 2100000, 700000, 1100000, 
                650000, 600000, 750000, 850000, 900000, 950000, 
                2400000, 3200000, 2800000, 2000000, 500000, 400000, 
                450000, 500000, 600000]

# Creating the DataFrame
data = {'Area': area_names, 'Price': house_prices}
house_prices_df = pd.DataFrame(data)
print(house_prices_df)

# Find the area with the highest price
highest_price_area = house_prices_df.loc[house_prices_df['Price'].idxmax()]
print("The area with the highest price is:", highest_price_area)

# Store the DataFrame in memory
tmp_dict = {'house_prices_df': house_prices_df}
pickle.dump(tmp_dict, open('tmp/memory.pkl', 'wb'))
