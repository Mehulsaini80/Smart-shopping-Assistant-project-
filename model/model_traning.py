import mysql.connector
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, RandomForestClassifier
from xgboost import XGBRegressor, XGBClassifier
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error, accuracy_score, classification_report
import pickle
import warnings
warnings.filterwarnings('ignore')
 
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Mehulmysql@90',
    'database': 'project_smart' 
}

def connect_to_database(): 
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        print("✅ Connected to MySQL database successfully!")
        return connection
    except mysql.connector.Error as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def load_data_from_db():
    try:
        connection = connect_to_database()
        if connection is None:
            return None
        
        query = "SELECT * FROM products"
        df = pd.read_sql(query, connection)
        
        print(f"✅ Data loaded successfully! Shape: {df.shape}")
        print(f"\nColumns: {df.columns.tolist()}")
        print(f"\nFirst few rows:\n{df.head()}")
        
        connection.close()
        return df
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None

def preprocess_data(df):
    print("\n[Processing] Preprocessing data...")
    
    # Create a copy to avoid modifying original
    df = df.copy()
    
    # Encode categorical variables
    label_encoders = {}
    
    # Encode platform
    le_platform = LabelEncoder()
    df['platform_encoded'] = le_platform.fit_transform(df['platform'])
    label_encoders['platform'] = le_platform
    
    # Encode category
    le_category = LabelEncoder()
    df['category_encoded'] = le_category.fit_transform(df['category'])
    label_encoders['category'] = le_category
    
    # Feature engineering
    df['price_range'] = pd.cut(df['price'], bins=[0, 1000, 5000, 15000, 30000, 100000], 
                                labels=[0, 1, 2, 3, 4])
    df['price_range'] = df['price_range'].astype(int)
    
    # Discount effectiveness
    df['discount_effectiveness'] = (df['price'] - df['discounted_price']) / df['price']
    
    # High discount flag (>20%)
    df['high_discount'] = (df['discount_percent'] > 20).astype(int)
    
    # Rating category
    df['rating_category'] = pd.cut(df['rating'], bins=[0, 3.5, 4.0, 4.5, 5.0], 
                                    labels=[0, 1, 2, 3])
    df['rating_category'] = df['rating_category'].astype(int)
    
    # Stock status
    df['stock_status'] = pd.cut(df['stock'], bins=[0, 50, 150, 300, 500], 
                                 labels=[0, 1, 2, 3])
    df['stock_status'] = df['stock_status'].astype(int)
    
    print(f"✅ Preprocessing complete! Final shape: {df.shape}")
    print(f"\nPlatform mapping: {dict(zip(le_platform.classes_, le_platform.transform(le_platform.classes_)))}")
    print(f"Category mapping: {dict(zip(le_category.classes_, le_category.transform(le_category.classes_)))}")
    
    return df, label_encoders

def train_discount_model(df, label_encoders):
    """Train model to predict discount percentage"""
    print("\n" + "="*70)
    print("TRAINING DISCOUNT PREDICTION MODEL (Regression)")
    print("="*70)
    
    # Features for discount prediction
    feature_cols = ['platform_encoded', 'category_encoded', 'price', 
                    'rating', 'stock', 'price_range', 'rating_category', 'stock_status']
    
    X = df[feature_cols]
    y = df['discount_percent']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train multiple models
    models = {
        'Linear Regression': LinearRegression(),
        'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10),
        'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, random_state=42, max_depth=5),
        'XGBoost': XGBRegressor(n_estimators=100, random_state=42, max_depth=6, learning_rate=0.1)
    }
    
    best_model = None
    best_score = -float('inf')
    best_name = ""
    
    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train_scaled, y_train)
        
        y_pred = model.predict(X_test_scaled)
        
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"  RMSE: {rmse:.4f}")
        print(f"  MAE: {mae:.4f}")
        print(f"  R² Score: {r2:.4f}")
        
        if r2 > best_score:
            best_score = r2
            best_model = model
            best_name = name
    
    print(f"\n🏆 Best Discount Model: {best_name} (R² = {best_score:.4f})")
    
    return best_model, scaler, feature_cols, best_name

def train_platform_model(df, label_encoders):
    """Train model to predict best platform"""
    print("\n" + "="*70)
    print("TRAINING PLATFORM PREDICTION MODEL (Classification)")
    print("="*70)
    
    # Features for platform prediction
    feature_cols = ['category_encoded', 'price', 'discount_percent', 
                    'rating', 'stock', 'price_range', 'discount_effectiveness']
    
    X = df[feature_cols]
    y = df['platform_encoded']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest (best for multi-class classification)
    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    
    print("\nTraining Random Forest Classifier...")
    model.fit(X_train_scaled, y_train)
    
    y_pred = model.predict(X_test_scaled)
    
    accuracy = accuracy_score(y_test, y_pred)
    print(f"  Accuracy: {accuracy:.4f}")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, 
                                target_names=label_encoders['platform'].classes_))
    
    return model, scaler, feature_cols

def save_models(discount_model, discount_scaler, discount_features, discount_name,
                platform_model, platform_scaler, platform_features, label_encoders):
    """Save all trained models and preprocessing objects"""
    print("\n[Saving] Saving models and encoders...")
    
    # Save discount prediction model
    with open('discount_model.pkl', 'wb') as f:
        pickle.dump(discount_model, f)
    print("✅ Discount model saved: discount_model.pkl")
    
    with open('discount_scaler.pkl', 'wb') as f:
        pickle.dump(discount_scaler, f)
    print("✅ Discount scaler saved: discount_scaler.pkl")
    
    with open('discount_features.pkl', 'wb') as f:
        pickle.dump(discount_features, f)
    print("✅ Discount features saved: discount_features.pkl")
    
    # Save platform prediction model
    with open('platform_model.pkl', 'wb') as f:
        pickle.dump(platform_model, f)
    print("✅ Platform model saved: platform_model.pkl")
    
    with open('platform_scaler.pkl', 'wb') as f:
        pickle.dump(platform_scaler, f)
    print("✅ Platform scaler saved: platform_scaler.pkl")
    
    with open('platform_features.pkl', 'wb') as f:
        pickle.dump(platform_features, f)
    print("✅ Platform features saved: platform_features.pkl")
    
    # Save label encoders
    with open('label_encoders.pkl', 'wb') as f:
        pickle.dump(label_encoders, f)
    print("✅ Label encoders saved: label_encoders.pkl")
    
    # Save model metadata
    metadata = {
        'discount_model_name': discount_name,
        'platform_model_name': 'Random Forest Classifier'
    }
    with open('model_metadata.pkl', 'wb') as f:
        pickle.dump(metadata, f)
    print("✅ Model metadata saved: model_metadata.pkl")

def main():
    print("="*70)
    print("PRODUCT DISCOUNT & PLATFORM PREDICTOR - ML MODEL TRAINING")
    print("="*70)
    
    # Step 1: Load data
    print("\n[1/4] Loading data from database...")
    df = load_data_from_db()
    
    if df is None or len(df) == 0:
        print("❌ No data available. Please ensure products table has data.")
        return
    
    print(f"Loaded {len(df)} products from database")
    
    # Step 2: Preprocess data
    print("\n[2/4] Preprocessing data...")
    df, label_encoders = preprocess_data(df)
    
    # Step 3: Train discount prediction model
    print("\n[3/4] Training discount prediction model...")
    discount_model, discount_scaler, discount_features, discount_name = train_discount_model(df, label_encoders)
    
    # Train platform prediction model
    print("\n[3/4] Training platform prediction model...")
    platform_model, platform_scaler, platform_features = train_platform_model(df, label_encoders)
    
    # Step 4: Save models
    print("\n[4/4] Saving models...")
    save_models(discount_model, discount_scaler, discount_features, discount_name,
                platform_model, platform_scaler, platform_features, label_encoders)
    
    # Summary
    print("\n" + "="*70)
    print("✅ TRAINING COMPLETED SUCCESSFULLY!")
    print("="*70)
    print(f"\n🎯 Discount Model: {discount_name}")
    print(f"🎯 Platform Model: Random Forest Classifier")
    print(f"📊 Total Products: {len(df)}")
    print(f"\n📦 Files saved:")
    print(f"   - discount_model.pkl")
    print(f"   - discount_scaler.pkl")
    print(f"   - discount_features.pkl")
    print(f"   - platform_model.pkl")
    print(f"   - platform_scaler.pkl")
    print(f"   - platform_features.pkl")
    print(f"   - label_encoders.pkl")
    print(f"   - model_metadata.pkl")
    print("\n✨ You can now run the Flask app with: python app.py")

if __name__ == "__main__":

    main()
