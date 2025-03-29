
import pandas as pd
import pickle

# Load the dataset
file_path = 'tmp/tmp/uae_real_estate_2024.csv'
df = pd.read_csv(file_path)

# Check the first few rows to confirm data structure
print("Dataset Preview:")
print(df.head())

# Find the top 10 most expensive properties using the 'price' column
top_10_expensive_properties = df.nlargest(10, 'price')
result = top_10_expensive_properties[['price', 'displayAddress', 'type', 'bedrooms', 'bathrooms']]

# Print the result
print("Top 10 Most Expensive Properties:")
print(result)

# Save the result to memory
our_dict = pickle.load(open('tmp/memory.pkl', 'rb'))  # Accessing existing memory
our_dict['top_10_expensive_properties'] = result  # Storing the result
pickle.dump(our_dict, open('tmp/memory.pkl', 'wb'))  # Saving back to memory
