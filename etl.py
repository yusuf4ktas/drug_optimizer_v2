import csv
import sqlite3
import os
import re
from collections import defaultdict
from database import DrugDatabase

DATA_DIR = 'data'


class DrugETL:
    def __init__(self, db_class):
        self.db = db_class

    def load_csv_to_db(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()

        def get_path(filename):
            return os.path.join(DATA_DIR, filename)

        print("Starting Full ETL Process...")

        def load_table(filename, table_name, csv_keys, db_columns=None):
            """
            Generic loader for standard CSVs.
            """
            p = get_path(filename)
            if not os.path.exists(p):
                print(f"Skipping {filename} (not found)")
                return

            if db_columns is None:
                db_columns = csv_keys

            print(f"Loading {table_name}...")
            with open(p, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                to_db = []
                for row in reader:
                    # Safely get data, defaulting to empty string if missing
                    data = tuple(row.get(k, '') for k in csv_keys)
                    to_db.append(data)

            if not to_db:
                print(f" - No data found in {filename}.")
                return

            placeholders = ', '.join(['?'] * len(db_columns))
            query = f"INSERT INTO {table_name} ({', '.join(db_columns)}) VALUES ({placeholders})"

            try:
                cursor.executemany(query, to_db)
            except sqlite3.OperationalError as e:
                print(f"Error loading {table_name}: {e}")
                # Optional: raise e if you want to stop on error

        # Load Drugs (Custom logic for PRIMARY KEY replacement)
        path = get_path('drugs.csv')
        if os.path.exists(path):
            print("Loading Drugs...")
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                keys = ['drugbank_id', 'name', 'type', 'cas_number', 'groups', 'description', 'moa', 'half_life',
                        'clearance']
                to_db = [tuple(row.get(k, '') for k in keys) for row in reader]

            # Using INSERT OR REPLACE to handle potential re-runs
            placeholders = ', '.join(['?'] * len(keys))
            cursor.executemany(
                f"INSERT OR REPLACE INTO drugs ({', '.join(keys)}) VALUES ({placeholders})",
                to_db
            )
        else:
            print(f"Skipping drugs.csv (not found)")

        # 2. Indications
        load_table('drug_indications.csv', 'indications',
                   csv_keys=['drugbank_id', 'indication_text'])

        # 3. Interactions
        load_table('drug_interactions.csv', 'interactions',
                   csv_keys=['drugbank_id', 'target_drug_id', 'target_drug_name', 'description'])

        # 4. Food Interactions
        load_table('food_interactions.csv', 'food_interactions',
                   csv_keys=['drugbank_id', 'interaction_text'])

        # 5. Toxicity
        load_table('drug_toxicity.csv', 'toxicity',
                   csv_keys=['drugbank_id', 'toxicity_text'])

        # 6. Synonyms
        load_table('drug_synonyms.csv', 'synonyms',
                   csv_keys=['drugbank_id', 'synonym', 'language', 'coder'])

        # 7. SNP Adverse Reactions
        load_table('snp_adverse_reactions.csv', 'snp_adverse_reactions',
                   csv_keys=['drugbank_id', 'protein_name', 'gene_symbol', 'adverse_reaction', 'description'])

        # 8. Enzymes
        load_table('drug_enzymes.csv', 'enzymes',
                   csv_keys=['drugbank_id', 'enzyme_id', 'enzyme_name', 'organism', 'action', 'inhibition_strength',
                             'induction_strength'])

        # 9. Targets
        load_table('drug_targets.csv', 'targets',
                   csv_keys=['drugbank_id', 'target_id', 'target_name', 'organism', 'known_action'])

        # 10. Prices
        price_path = get_path('drug_prices.csv')
        if os.path.exists(price_path):
            print("Loading Prices (Selecting representative price per drug)...")

            # Helper to clean price string to float
            def parse_cost(c_str):
                try:
                    return float(re.sub(r'[^\d.]', '', c_str))
                except:
                    return float('inf')

            # Helper to rank units, lower is better
            def rank_unit(u_str):
                u = u_str.lower()
                if 'tablet' in u or 'capsule' in u: return 1
                if 'ml' in u or 'liquid' in u or 'solution' in u: return 2
                return 3

            price_map = defaultdict(list)

            with open(price_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    did = row.get('drugbank_id')
                    if did:
                        price_map[did].append(row)

            to_db_prices = []

            for did, entries in price_map.items():
                # Filter for USD if available
                usd_entries = [e for e in entries if e.get('currency') == 'USD']
                candidates = usd_entries if usd_entries else entries

                # Sort by Unit Rank (Tablet first), then Cost (Lowest first)
                candidates.sort(key=lambda x: (
                    rank_unit(x.get('unit', '')),
                    parse_cost(x.get('cost', ''))
                ))

                # Select best candidate
                best = candidates[0]
                to_db_prices.append((
                    best['drugbank_id'],
                    best.get('description', ''),
                    best.get('cost', ''),
                    best.get('currency', ''),
                    best.get('unit', '')
                ))

            cursor.executemany(
                "INSERT INTO prices (drugbank_id, description, cost, currency, unit) VALUES (?, ?, ?, ?, ?)",
                to_db_prices
            )
        else:
            print("Skipping drug_prices.csv (not found)")

        # 11. Products
        load_table('drug_products.csv', 'products',
                   csv_keys=['drugbank_id', 'product_name', 'labeller', 'dosage_form', 'strength', 'route', 'country'])

        # 12. Categories
        load_table('drug_categories.csv', 'categories',
                   csv_keys=['drugbank_id', 'category', 'mesh_id'])

        # 13. Transporters
        load_table('drug_transporters.csv', 'transporters',
                   csv_keys=['drugbank_id', 'transporter_id', 'transporter_name', 'organism', 'actions'])

        # 14. Carriers
        load_table('drug_carriers.csv', 'carriers',
                   csv_keys=['drugbank_id', 'carrier_id', 'carrier_name', 'organism', 'actions'])

        # 15. Pathways
        load_table('drug_pathways.csv', 'pathways',
                   csv_keys=['drugbank_id', 'smpdb_id', 'pathway_name', 'category'])

        # 16. Dosages
        load_table('drug_dosages.csv', 'dosages',
                   csv_keys=['drugbank_id', 'form', 'route', 'strength'])

        # 17. ATC Codes
        load_table('drug_atc_codes.csv', 'atc_codes',
                   csv_keys=['drugbank_id', 'atc_code', 'level_1', 'level_2', 'level_3', 'level_4'])

        conn.commit()
        conn.close()
        print("Full ETL Complete. All files loaded.")


if __name__ == "__main__":
    db = DrugDatabase()

    print("Ensuring database schema exists...")
    db.create_schema()

    etl = DrugETL(db)
    etl.load_csv_to_db()