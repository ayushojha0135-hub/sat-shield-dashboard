import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

# 1. Data Load Karein:
data = pd.read_csv('dataset.csv')
data = data.fillna(0)

# 2. Data Normalize Karein:
scaler = MinMaxScaler()
numeric_cols = data.select_dtypes(include=['number']).columns
data[numeric_cols] = scaler.fit_transform(data[numeric_cols])

# 3. Features (X) aur Target (y) Alag Karein (Channel aur anomaly hata kar):
X = data.drop(columns=['anomaly', 'channel'])  
y = data['anomaly']

# 4. Train aur Test Split Karein:
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

from tensorflow.keras.layers import Dropout

# 5. Model Define Karein (Powerful Architecture):
number_of_features = X.shape[1]

model = Sequential([
    Dense(128, activation='relu', input_shape=(number_of_features,)),
    Dropout(0.3), # Overfitting se bachane ke liye
    Dense(64, activation='relu'),
    Dropout(0.2),
    Dense(32, activation='relu'),
    Dense(1, activation='sigmoid') # 1 for Attack, 0 for Normal
])

# 6. Model Compile Karein:
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# 7. Model Train Karein (Epochs 50 kar diye hain):
history = model.fit(X_train, y_train, epochs=50, batch_size=32, validation_split=0.2)


# 8. Model Evaluate Karein:
loss, accuracy = model.evaluate(X_test, y_test)
print(f"Test Accuracy: {accuracy * 100:.2f}%")

# 9. Model Save Karein:
model.save('satellite_cybersecurity_model.h5')
print("Model successfully saved as satellite_cybersecurity_model.h5")
# --- Self-Healing System Logic ---
def self_healing_protocol(prediction):
    if prediction == 1:
        print("ALERT: Cyber Attack Detected! Initiating Self-Healing...")
        # Yahan aap frequency change karne ka ya backup channel par switch karne ka code likh sakte hain
        print("Switching to secure backup channel.")
    else:
        print("System Normal. Satellite is safe.")

# Model se ek test prediction lekar check karte hain:
import numpy as np
sample_data = X_test.iloc[0:1] # Test data ka pehla sample
prediction_prob = model.predict(sample_data)
predicted_class = 1 if prediction_prob[0][0] > 0.5 else 0

# Self-healing function ko call karein
self_healing_protocol(predicted_class)
