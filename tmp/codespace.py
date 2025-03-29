
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler
import pickle

# Load the dataset
print("Loading the UAE properties dataset...")
uae_data = pd.read_csv('tmp/tmp/uae_properties.csv')

# Display the first few rows of the dataset
print("UAE properties dataset loaded:")
print(uae_data.head())

# Check for missing values
print("Checking for missing values...")
print(uae_data.isnull().sum())

# Drop rows with missing target variable
uae_data = uae_data.dropna(subset=['price'])

# Fill missing values in numeric columns with the median
uae_data.fillna(uae_data.median(numeric_only=True), inplace=True)

# Identify and remove outliers using the IQR method
Q1 = uae_data['price'].quantile(0.25)
Q3 = uae_data['price'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

# Filter out outliers
uae_data = uae_data[(uae_data['price'] >= lower_bound) & (uae_data['price'] <= upper_bound)]
print(f"Data shape after removing outliers: {uae_data.shape}")

# Prepare features and target variable
X = uae_data.drop(['price'], axis=1)
y = uae_data['price']

# Encode categorical variables
X = pd.get_dummies(X, drop_first=True)

# Split the data into training and test sets
print("Splitting the data into training and test sets...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Feature Scaling
print("Applying feature scaling...")
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Tune the Random Forest model using Grid Search
print("Tuning the Random Forest Regressor model using Grid Search...")
param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [None, 10, 20, 30],
    'min_samples_split': [2, 5, 10]
}

grid_search = GridSearchCV(RandomForestRegressor(random_state=42), param_grid, cv=3, n_jobs=-1, verbose=2)
grid_search.fit(X_train, y_train)

# Get the best model from grid search
best_model = grid_search.best_estimator_
print(f"Best model parameters: {grid_search.best_params_}")

# Evaluate the model
print("Evaluating the best model on the test set...")
y_pred = best_model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
accuracy = 1 - np.sqrt(mse) / np.mean(y_test)

print(f"Mean Squared Error: {mse}")
print(f"Accuracy: {accuracy * 100:.2f}%")

# Check if the model meets the accuracy requirement
if accuracy >= 0.80:
    print("Model achieved over 80% accuracy.")
    our_dict = {}
    our_dict['uae_model'] = best_model
    pickle.dump(our_dict, open('tmp/memory.pkl', 'wb'))
    print("Model saved successfully!")
else:
    print("Model did not achieve the required accuracy. Further optimization may be needed.")
    
    # Consider alternate hyperparameters or models
    print("Attempting additional hyperparameter tuning...")
    param_grid_2 = {
        'n_estimators': [200, 400],
        'max_depth': [20, 40],
        'min_samples_split': [2, 10]
    }

    grid_search_2 = GridSearchCV(RandomForestRegressor(random_state=42), param_grid_2, cv=3, n_jobs=-1, verbose=2)
    grid_search_2.fit(X_train, y_train)

    # Get the best model from grid search
    best_model_2 = grid_search_2.best_estimator_
    print(f"Best model parameters after second tuning: {grid_search_2.best_params_}")

    # Evaluate the new model
    print("Evaluating the new model on the test set...")
    y_pred_2 = best_model_2.predict(X_test)
    mse_2 = mean_squared_error(y_test, y_pred_2)
    accuracy_2 = 1 - np.sqrt(mse_2) / np.mean(y_test)

    print(f"Mean Squared Error for new model: {mse_2}")
    print(f"Accuracy for new model: {accuracy_2 * 100:.2f}%")

    if accuracy_2 >= 0.80:
        print("New model achieved over 80% accuracy.")
        our_dict['uae_model'] = best_model_2
        pickle.dump(our_dict, open('tmp/memory.pkl', 'wb'))
        print("New model saved successfully!")
    else:
        print("New model did not achieve the required accuracy.")

"""
