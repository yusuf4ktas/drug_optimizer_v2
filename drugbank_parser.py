import csv
import xml.etree.ElementTree as ET
import os

# Define the source XML file
XML_FILE = 'data/database.xml'
NS = {'db': 'http://www.drugbank.ca'}


def get_text(element, path):
    """Helper to safely extract text from an element using the namespace."""
    found = element.find(path, NS)
    return found.text if found is not None and found.text else ""


def get_primary_id(drug_element):
    ids = drug_element.findall('db:drugbank-id', NS)
    for existing_id in ids:
        if existing_id.get('primary') == 'true':
            return existing_id.text
    return ids[0].text if ids else "Unknown"


def parse_drugbank_xml(xml_file):
    if not os.path.exists(xml_file):
        print(f"Error: {xml_file} not found.")
        return

    print(f"Processing {xml_file}...")

    # Open CSV files
    files = {
        'drugs': open('data/drugs.csv', 'w', newline='', encoding='utf-8'),
        'indications': open('data/drug_indications.csv', 'w', newline='', encoding='utf-8'),
        'interactions': open('data/drug_interactions.csv', 'w', newline='', encoding='utf-8'),
        'synonyms': open('data/drug_synonyms.csv', 'w', newline='', encoding='utf-8'),
        'food': open('data/food_interactions.csv', 'w', newline='', encoding='utf-8'),
        'toxicity': open('data/drug_toxicity.csv', 'w', newline='', encoding='utf-8'),
        'snp_adverse': open('data/snp_adverse_reactions.csv', 'w', newline='', encoding='utf-8'),
        'enzymes': open('data/drug_enzymes.csv', 'w', newline='', encoding='utf-8'),
        'targets': open('data/drug_targets.csv', 'w', newline='', encoding='utf-8'),
        'prices': open('data/drug_prices.csv', 'w', newline='', encoding='utf-8'),
        'products': open('data/drug_products.csv', 'w', newline='', encoding='utf-8'),
        'categories': open('data/drug_categories.csv', 'w', newline='', encoding='utf-8'),
        'transporters': open('data/drug_transporters.csv', 'w', newline='', encoding='utf-8'),
        'carriers': open('data/drug_carriers.csv', 'w', newline='', encoding='utf-8'),
        'pathways': open('data/drug_pathways.csv', 'w', newline='', encoding='utf-8'),
        'dosages': open('data/drug_dosages.csv', 'w', newline='', encoding='utf-8'),
        'atc_codes': open('data/drug_atc_codes.csv', 'w', newline='', encoding='utf-8')
    }

    writers = {}

    # Main Drugs File
    writers['drugs'] = csv.writer(files['drugs'])
    writers['drugs'].writerow(
        ['drugbank_id', 'name', 'type', 'cas_number', 'groups', 'description', 'moa', 'half_life', 'clearance'])

    writers['indications'] = csv.writer(files['indications'])
    writers['indications'].writerow(['drugbank_id', 'indication_text'])

    writers['interactions'] = csv.writer(files['interactions'])
    writers['interactions'].writerow(['drugbank_id', 'target_drug_id', 'target_drug_name', 'description'])

    writers['synonyms'] = csv.writer(files['synonyms'])
    writers['synonyms'].writerow(['drugbank_id', 'synonym', 'language', 'coder'])

    writers['food'] = csv.writer(files['food'])
    writers['food'].writerow(['drugbank_id', 'interaction_text'])

    writers['toxicity'] = csv.writer(files['toxicity'])
    writers['toxicity'].writerow(['drugbank_id', 'toxicity_text'])

    writers['snp_adverse'] = csv.writer(files['snp_adverse'])
    writers['snp_adverse'].writerow(['drugbank_id', 'protein_name', 'gene_symbol', 'adverse_reaction', 'description'])

    # Enzymes
    writers['enzymes'] = csv.writer(files['enzymes'])
    writers['enzymes'].writerow(
        ['drugbank_id', 'enzyme_id', 'enzyme_name', 'organism', 'action', 'inhibition_strength', 'induction_strength'])

    # Targets
    writers['targets'] = csv.writer(files['targets'])
    writers['targets'].writerow(['drugbank_id', 'target_id', 'target_name', 'organism', 'known_action'])

    writers['prices'] = csv.writer(files['prices'])
    writers['prices'].writerow(['drugbank_id', 'description', 'cost', 'currency', 'unit'])

    writers['products'] = csv.writer(files['products'])
    writers['products'].writerow(
        ['drugbank_id', 'product_name', 'labeller', 'dosage_form', 'strength', 'route', 'country'])

    writers['categories'] = csv.writer(files['categories'])
    writers['categories'].writerow(['drugbank_id', 'category', 'mesh_id'])

    # Transporters
    writers['transporters'] = csv.writer(files['transporters'])
    writers['transporters'].writerow(['drugbank_id', 'transporter_id', 'transporter_name', 'organism', 'actions'])

    # Carriers
    writers['carriers'] = csv.writer(files['carriers'])
    writers['carriers'].writerow(['drugbank_id', 'carrier_id', 'carrier_name', 'organism', 'actions'])

    writers['pathways'] = csv.writer(files['pathways'])
    writers['pathways'].writerow(['drugbank_id', 'smpdb_id', 'pathway_name', 'category'])

    writers['dosages'] = csv.writer(files['dosages'])
    writers['dosages'].writerow(['drugbank_id', 'form', 'route', 'strength'])

    writers['atc_codes'] = csv.writer(files['atc_codes'])
    writers['atc_codes'].writerow(['drugbank_id', 'atc_code', 'level_1', 'level_2', 'level_3', 'level_4'])

    context = ET.iterparse(xml_file, events=('end',))

    try:
        for event, elem in context:
            if elem.tag == f"{{{NS['db']}}}drug":
                db_id = get_primary_id(elem)
                name = get_text(elem, 'db:name')
                drug_type = elem.get('type', '')
                cas_number = get_text(elem, 'db:cas-number')
                description = get_text(elem, 'db:description')
                moa = get_text(elem, 'db:mechanism-of-action')

                # Capture PK data for safety checks
                half_life = get_text(elem, 'db:half-life')
                clearance = get_text(elem, 'db:clearance')

                groups = [g.text for g in elem.findall('db:groups/db:group', NS)]
                groups_str = "; ".join(groups)

                writers['drugs'].writerow(
                    [db_id, name, drug_type, cas_number, groups_str, description, moa, half_life, clearance])

                # Indication
                indication_text = get_text(elem, 'db:indication')
                if indication_text:
                    writers['indications'].writerow([db_id, indication_text])

                # Toxicity
                toxicity_text = get_text(elem, 'db:toxicity')
                if toxicity_text:
                    writers['toxicity'].writerow([db_id, toxicity_text])

                # Drug Interactions
                for interact in elem.findall('db:drug-interactions/db:drug-interaction', NS):
                    target_id = get_text(interact, 'db:drugbank-id')
                    target_name = get_text(interact, 'db:name')
                    desc = get_text(interact, 'db:description')
                    writers['interactions'].writerow([db_id, target_id, target_name, desc])

                # Synonyms
                for syn in elem.findall('db:synonyms/db:synonym', NS):
                    writers['synonyms'].writerow([db_id, syn.text, syn.get('language', ''), syn.get('coder', '')])

                # Food Interactions
                for food in elem.findall('db:food-interactions/db:food-interaction', NS):
                    writers['food'].writerow([db_id, food.text])

                # SNP Adverse Reactions
                for snp in elem.findall('db:snp-adverse-drug-reactions/db:reaction', NS):
                    writers['snp_adverse'].writerow([
                        db_id,
                        get_text(snp, 'db:protein-name'),
                        get_text(snp, 'db:gene-symbol'),
                        get_text(snp, 'db:adverse-reaction'),
                        get_text(snp, 'db:description')
                    ])

                # Enzymes
                for enz in elem.findall('db:enzymes/db:enzyme', NS):
                    actions = [a.text for a in enz.findall('db:actions/db:action', NS)]
                    writers['enzymes'].writerow([
                        db_id,
                        get_text(enz, 'db:id'),
                        get_text(enz, 'db:name'),
                        get_text(enz, 'db:organism'),
                        "; ".join(actions),
                        get_text(enz, 'db:inhibition-strength'),
                        get_text(enz, 'db:induction-strength')
                    ])

                # Targets
                for tgt in elem.findall('db:targets/db:target', NS):
                    writers['targets'].writerow([
                        db_id,
                        get_text(tgt, 'db:id'),
                        get_text(tgt, 'db:name'),
                        get_text(tgt, 'db:organism'),
                        get_text(tgt, 'db:known-action')
                    ])

                # Prices
                for price in elem.findall('db:prices/db:price', NS):
                    cost_elem = price.find('db:cost', NS)
                    cost = cost_elem.text if cost_elem is not None else ""
                    curr = cost_elem.get('currency', '') if cost_elem is not None else ""
                    writers['prices'].writerow(
                        [db_id, get_text(price, 'db:description'), cost, curr, get_text(price, 'db:unit')])

                # Products
                for prod in elem.findall('db:products/db:product', NS):
                    country = prod.find('db:country', NS)
                    c_text = country.text if country is not None else ""
                    writers['products'].writerow([
                        db_id,
                        get_text(prod, 'db:name'),
                        get_text(prod, 'db:labeller'),
                        get_text(prod, 'db:dosage-form'),
                        get_text(prod, 'db:strength'),
                        get_text(prod, 'db:route'),
                        c_text
                    ])

                # Categories
                for cat in elem.findall('db:categories/db:category', NS):
                    writers['categories'].writerow([db_id, get_text(cat, 'db:category'), get_text(cat, 'db:mesh-id')])

                # Transporters - Updated for Organism
                for trans in elem.findall('db:transporters/db:transporter', NS):
                    actions = [a.text for a in trans.findall('db:actions/db:action', NS)]
                    writers['transporters'].writerow([
                        db_id,
                        get_text(trans, 'db:id'),
                        get_text(trans, 'db:name'),
                        get_text(trans, 'db:organism'),
                        "; ".join(actions)
                    ])

                # Carriers
                for carr in elem.findall('db:carriers/db:carrier', NS):
                    actions = [a.text for a in carr.findall('db:actions/db:action', NS)]
                    writers['carriers'].writerow([
                        db_id,
                        get_text(carr, 'db:id'),
                        get_text(carr, 'db:name'),
                        get_text(carr, 'db:organism'),
                        "; ".join(actions)
                    ])

                # Pathways
                for path in elem.findall('db:pathways/db:pathway', NS):
                    writers['pathways'].writerow([db_id, get_text(path, 'db:smpdb-id'), get_text(path, 'db:name'),
                                                  get_text(path, 'db:category')])

                # Dosages
                for dose in elem.findall('db:dosages/db:dosage', NS):
                    writers['dosages'].writerow(
                        [db_id, get_text(dose, 'db:form'), get_text(dose, 'db:route'), get_text(dose, 'db:strength')])

                # ATC Codes
                for atc in elem.findall('db:atc-codes/db:atc-code', NS):
                    levels = atc.findall('db:level', NS)
                    writers['atc_codes'].writerow([
                        db_id,
                        atc.get('code', ''),
                        levels[0].text if len(levels) > 0 else "",
                        levels[1].text if len(levels) > 1 else "",
                        levels[2].text if len(levels) > 2 else "",
                        levels[3].text if len(levels) > 3 else ""
                    ])

                elem.clear()

    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
    finally:
        for f in files.values():
            f.close()
        print("Extraction complete.")


if __name__ == "__main__":
    parse_drugbank_xml(XML_FILE)