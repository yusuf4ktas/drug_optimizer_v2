import sqlite3
import os

DB_NAME = 'drug_project.db'

class DrugDatabase:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def create_schema(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Drugs (Core Info)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drugs (
                drugbank_id TEXT PRIMARY KEY,
                name TEXT,
                type TEXT,
                cas_number TEXT,
                groups TEXT,
                description TEXT,
                moa TEXT,
                half_life TEXT,
                clearance TEXT
            )
        ''')

        # Indications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS indications (
                drugbank_id TEXT,
                indication_text TEXT,
                FOREIGN KEY(drugbank_id) REFERENCES drugs(drugbank_id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_indications ON indications(indication_text)')

        # Interactions (Drug-Drug)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                drugbank_id TEXT,
                target_drug_id TEXT,
                target_drug_name TEXT,
                description TEXT,
                FOREIGN KEY(drugbank_id) REFERENCES drugs(drugbank_id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions ON interactions(drugbank_id, target_drug_id)')

        # Food Interactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS food_interactions (
                drugbank_id TEXT,
                interaction_text TEXT,
                FOREIGN KEY(drugbank_id) REFERENCES drugs(drugbank_id)
            )
        ''')

        # Toxicity
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS toxicity (
                drugbank_id TEXT,
                toxicity_text TEXT,
                FOREIGN KEY(drugbank_id) REFERENCES drugs(drugbank_id)
            )
        ''')

        # Synonyms
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS synonyms (
                drugbank_id TEXT,
                synonym TEXT,
                language TEXT,
                coder TEXT,
                FOREIGN KEY(drugbank_id) REFERENCES drugs(drugbank_id)
            )
        ''')

        # SNP Adverse Reactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS snp_adverse_reactions (
                drugbank_id TEXT,
                protein_name TEXT,
                gene_symbol TEXT,
                adverse_reaction TEXT,
                description TEXT,
                FOREIGN KEY(drugbank_id) REFERENCES drugs(drugbank_id)
            )
        ''')

        # Enzymes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enzymes (
                drugbank_id TEXT,
                enzyme_id TEXT,
                enzyme_name TEXT,
                organism TEXT,
                action TEXT,
                inhibition_strength TEXT,
                induction_strength TEXT,
                FOREIGN KEY(drugbank_id) REFERENCES drugs(drugbank_id)
            )
        ''')

        # Targets
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS targets (
                drugbank_id TEXT,
                target_id TEXT,
                target_name TEXT,
                organism TEXT,
                known_action TEXT,
                FOREIGN KEY(drugbank_id) REFERENCES drugs(drugbank_id)
            )
        ''')

        # Prices
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                drugbank_id TEXT,
                description TEXT,
                cost TEXT,
                currency TEXT,
                unit TEXT,
                FOREIGN KEY(drugbank_id) REFERENCES drugs(drugbank_id)
            )
        ''')

        # Products
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                drugbank_id TEXT,
                product_name TEXT,
                labeller TEXT,
                dosage_form TEXT,
                strength TEXT,
                route TEXT,
                country TEXT,
                FOREIGN KEY(drugbank_id) REFERENCES drugs(drugbank_id)
            )
        ''')

        # Categories
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                drugbank_id TEXT,
                category TEXT,
                mesh_id TEXT,
                FOREIGN KEY(drugbank_id) REFERENCES drugs(drugbank_id)
            )
        ''')

        # Transporters
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transporters (
                drugbank_id TEXT,
                transporter_id TEXT,
                transporter_name TEXT,
                organism TEXT,
                actions TEXT,
                FOREIGN KEY(drugbank_id) REFERENCES drugs(drugbank_id)
            )
        ''')

        # Carriers
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carriers (
                drugbank_id TEXT,
                carrier_id TEXT,
                carrier_name TEXT,
                organism TEXT,
                actions TEXT,
                FOREIGN KEY(drugbank_id) REFERENCES drugs(drugbank_id)
            )
        ''')

        # Pathways
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pathways (
                drugbank_id TEXT,
                smpdb_id TEXT,
                pathway_name TEXT,
                category TEXT,
                FOREIGN KEY(drugbank_id) REFERENCES drugs(drugbank_id)
            )
        ''')

        # Dosages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dosages (
                drugbank_id TEXT,
                form TEXT,
                route TEXT,
                strength TEXT,
                FOREIGN KEY(drugbank_id) REFERENCES drugs(drugbank_id)
            )
        ''')

        # ATC Codes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS atc_codes (
                drugbank_id TEXT,
                atc_code TEXT,
                level_1 TEXT,
                level_2 TEXT,
                level_3 TEXT,
                level_4 TEXT,
                FOREIGN KEY(drugbank_id) REFERENCES drugs(drugbank_id)
            )
        ''')

        conn.commit()
        conn.close()
        print(f"Database {self.db_name} schema fully initialized with all 17 tables.")

if __name__ == "__main__":
    if os.path.exists(DB_NAME):
        print(f"Note: '{DB_NAME}' already exists. Ensure it matches the new schema or delete it to rebuild.")

    db = DrugDatabase()
    db.create_schema()