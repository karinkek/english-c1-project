import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os

def analyze_c1_dataset():
    """Analyze the generated C1 vocabulary dataset"""
    
    # Find the latest dataset
    data_files = glob.glob('data/raw/c1_vocabulary_*.csv')
    if not data_files:
        print("❌ No dataset found. Please generate data first.")
        return None
    
    latest_file = max(data_files, key=os.path.getctime)
    df = pd.read_csv(latest_file)
    
    print("=== 📊 C1 VOCABULARY DATASET ANALYSIS ===")
    print(f"📁 File: {latest_file}")
    print(f"📐 Dataset shape: {df.shape}")
    
    # Basic statistics
    print(f"\n📈 BASIC STATISTICS:")
    print(f"   Total words: {len(df)}")
    print(f"   Average complexity: {df['complexity_level'].mean():.1f}/10")
    print(f"   Average word length: {df['word_length'].mean():.1f} letters")
    print(f"   Average usage frequency: {df['usage_frequency'].mean():.1f}%")
    
    # Category analysis
    print(f"\n📂 CATEGORY ANALYSIS:")
    category_stats = df['category'].value_counts()
    for category, count in category_stats.items():
        print(f"   {category}: {count} words")
    
    # Complexity analysis
    print(f"\n🎯 COMPLEXITY ANALYSIS:")
    complexity_stats = df['complexity_level'].value_counts().sort_index()
    for level, count in complexity_stats.items():
        print(f"   Level {level}: {count} words")
    
    # Most complex words
    print(f"\n🔥 MOST COMPLEX WORDS:")
    complex_words = df.nlargest(3, 'complexity_level')[['word', 'complexity_level', 'category']]
    for _, row in complex_words.iterrows():
        print(f"   {row['word']} (Level {row['complexity_level']}, {row['category']})")
    
    return df

def show_dataset_info(df):
    """Show basic dataset information"""
    if df is not None:
        print(f"\n📋 DATASET INFO:")
        print(df.info())
        print(f"\n🔢 NUMERICAL STATS:")
        print(df.describe())

if __name__ == "__main__":
    df = analyze_c1_dataset()
    show_dataset_info(df)
