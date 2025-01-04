# data_collection.py

import pandas as pd
import os

def save_to_csv(user_data, file_path="data_collection.csv"):
    """Save user data to CSV file."""
    if not os.path.exists(file_path):
        # Create the CSV file with column headers if it doesn't exist
        pd.DataFrame([user_data]).to_csv(file_path, index=False)
    else:
        # Append the user data to the existing CSV file
        pd.DataFrame([user_data]).to_csv(file_path, mode="a", header=False, index=False)
