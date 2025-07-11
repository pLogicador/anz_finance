import pandas as pd
from modules.dashboard.streamlit_app import run_dashboard
import streamlit as st
from config import OUTPUT_CSV

def main():
    df = pd.read_csv(OUTPUT_CSV)
    run_dashboard(df)

if __name__ == "__main__":
    main()
