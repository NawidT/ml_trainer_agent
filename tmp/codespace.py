
import pandas as pd
import pickle

# Load stored data (if any)
try:
    tmp_dict = pickle.load(open('tmp/memory.pkl', 'rb'))
    print("Loaded data from memory successfully.")
except FileNotFoundError:
    print("No previous data found, initializing an empty dictionary.")
    tmp_dict = {}

# Step 1: Use a sample URL for the dataset (replace with an actual dataset source later)
url = 'https://www.example.com/data/uae-house-prices.csv'  # Modify this with a valid dataset URL

# Attempt to load the dataset into a DataFrame
try:
    house_prices_df = pd.read_csv(url)  # This command may fail if the URL is invalid.
    print("Dataset loaded into DataFrame successfully.")

    # Store the DataFrame in memory
    tmp_dict['house_prices_df'] = house_prices_df
    print("DataFrame stored in memory successfully.")

    # Analyzing which area has the highest house prices
    if 'price' in house_prices_df.columns and 'area' in house_prices_df.columns:
        highest_price_area = house_prices_df.loc[house_prices_df['price'].idxmax(), 'area']
        tmp_dict['highest_price_area'] = highest_price_area
        print(f"The area with the highest house price is: {highest_price_area}")
    else:
        print("Required columns for analysis not found in the DataFrame.")

    # Save the updated memory
    pickle.dump(tmp_dict, open('tmp/memory.pkl', 'wb'))
    print("Updated memory stored successfully.")
except Exception as e:
    print(f"An error occurred while processing: {e}")
