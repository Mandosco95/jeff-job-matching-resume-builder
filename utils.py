import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def load_sample_data():
    """
    Generate sample data for demonstration purposes
    """
    # Create a sample dataframe
    np.random.seed(42)
    dates = pd.date_range('20230101', periods=100)
    df = pd.DataFrame({
        'date': dates,
        'value_a': np.random.randn(100).cumsum(),
        'value_b': np.random.randn(100).cumsum(),
        'category': np.random.choice(['A', 'B', 'C'], 100)
    })
    return df

def plot_time_series(df, column):
    """
    Create a time series plot
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    df.plot(x='date', y=column, ax=ax)
    ax.set_title(f'Time Series of {column}')
    ax.set_xlabel('Date')
    ax.set_ylabel('Value')
    return fig 