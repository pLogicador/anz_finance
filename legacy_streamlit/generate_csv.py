from modules.parsers.ofx_parser import parse_ofx_files
from modules.llm.categorizer import Categorizer
from modules.data.finance_data import preprocess_df
from config import DATA_FOLDER, OUTPUT_CSV

def main():
    print("🔍 Parsing OFX files...")
    df = parse_ofx_files(DATA_FOLDER)

    print("⚙️ Preprocessing data...")
    df = preprocess_df(df)

    print("🧠 Classifying transactions...")
    categorizer = Categorizer()
    df["Categorias"] = categorizer.classify(df["Descrição"].values)

    print(f"💾 Saving to {OUTPUT_CSV}...")
    df.to_csv(OUTPUT_CSV, index=False)

    print("✅ CSV file generated!")

if __name__ == "__main__":
    main()
