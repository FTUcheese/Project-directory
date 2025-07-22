# Import Packages (pandas, numpy, matplotlib.pyplot ONLY)
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Read the Dataframe (ckd.csv) and clean column names

df = pd.read_csv('ckd.csv')
df.columns = [col.strip().capitalize() for col in df.columns]  # Remove spaces, make 'Class' capitalized

# Create 3 variables and save the label, Hemoglobin, and Blood Glucose Random
label = df['Class']
hemo = df['Hemoglobin']
bgr = df['Blood glucose random']

# Plot a scatterplot of Hemoglobin and Blood Glucose Random
colors = ['red' if str(c).strip().lower() == 'ckd' else 'blue' for c in label]
plt.figure(figsize=(8, 6))
plt.scatter(hemo, bgr, c=colors, alpha=0.7)
plt.xlabel('Hemoglobin')
plt.ylabel('Blood Glucose Random')
plt.title('Hemoglobin vs Blood Glucose Random')
plt.savefig('plot1_scatter_raw.png')
plt.close()

# Create a function that normalizes the data - via Min-Max Normalization
def normalize(series):
    return (series - series.min()) / (series.max() - series.min())

# Normalize Hemoglobin and BGR
df['Hemoglobin_norm'] = normalize(df['Hemoglobin'])
df['Bgr_norm'] = normalize(df['Blood glucose random'])

# Plot normalized scatterplot
plt.figure(figsize=(8, 6))
plt.scatter(df['Hemoglobin_norm'], df['Bgr_norm'], c=colors, alpha=0.7)
plt.xlabel('Hemoglobin (Normalized)')
plt.ylabel('Blood Glucose Random (Normalized)')
plt.title('Normalized Hemoglobin vs Blood Glucose Random')
plt.savefig('plot2_scatter_normalized.png')
plt.close()

# Function to calculate Euclidean Distance from a new point to all dataset
def euclidean_distances(x, y, df):
    return np.sqrt((df['Hemoglobin_norm'] - x)**2 + (df['Bgr_norm'] - y)**2)

# Generate a new + random point (normalized 0-1)
np.random.seed(42)
rand_point = np.random.rand(2)  # (hemo_norm, bgr_norm)

# Use Nearest Neighbor Classification using this point
df['distance'] = euclidean_distances(rand_point[0], rand_point[1], df)
nearest_idx = df['distance'].idxmin()
neigh_class = df.loc[nearest_idx, 'Class']

# Plot the Nearest Neighbor Classification
plt.figure(figsize=(8, 6))
plt.scatter(df['Hemoglobin_norm'], df['Bgr_norm'], c=colors, alpha=0.7, label='Data Points')
plt.scatter(rand_point[0], rand_point[1], c='green', marker='*', s=200, label='Random Point')
plt.scatter(df.loc[nearest_idx, 'Hemoglobin_norm'], df.loc[nearest_idx, 'Bgr_norm'], c='orange', marker='x', s=150, label='Nearest Neighbor')
plt.xlabel('Hemoglobin (Normalized)')
plt.ylabel('Blood Glucose Random (Normalized)')
plt.title(f'Nearest Neighbor Classification (Predicted: {neigh_class})')
plt.legend()
plt.savefig('plot3_nearest_neighbor.png')
plt.close()

# Plot classes: different colors for different classes
plt.figure(figsize=(8, 6))
for cl, col in [('ckd', 'red'), ('notckd', 'blue')]:
    mask = df['Class'].str.strip().str.lower() == cl
    plt.scatter(df.loc[mask, 'Hemoglobin_norm'], df.loc[mask, 'Bgr_norm'], c=col, label=cl)
plt.xlabel('Hemoglobin (Normalized)')
plt.ylabel('Blood Glucose Random (Normalized)')
plt.title('Classes after Normalization')
plt.legend()
plt.savefig('plot4_classes.png')
plt.close()

# Also print the result to stdout for easy CLI reading
print('Random point:', rand_point)
print('Nearest Neighbor Class:', neigh_class)
print('Nearest Neighbor Index:', nearest_idx)
