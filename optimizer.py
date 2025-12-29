import sqlite3
import pulp
from collections import defaultdict
import re


class DrugOptimizer:
    def __init__(self, db_path):
        self.db_path = db_path

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _clean_price(self, p_str):
        if not p_str: return 0.0
        clean = re.sub(r'[^\d.]', '', str(p_str))
        try:
            return float(clean)
        except:
            return 0.0

    def _parse_half_life(self, hl_str):
        if not hl_str: return 0.0
        val = re.search(r'(\d+(\.\d+)?)', hl_str)
        if not val: return 0.0
        num = float(val.group(1))
        lower = hl_str.lower()
        if 'day' in lower: return num * 24
        if 'minute' in lower: return num / 60
        return num

    def _get_search_terms(self, condition, all_conditions_text):
        c_lower = condition.lower().strip()


        # Bacterial: Removed generic 'antibiotic' to avoid matches like Acetohydroxamic acid)
        if 'bacterial' in c_lower or 'infection' in c_lower:
            return [
                'penicillin', 'cephalosporin', 'fluoroquinolone', 'macrolide',
                'tetracycline', 'sulfonamide', 'aminoglycoside', 'carbapenem',
                'nitroimidazole', 'quinolone', 'lincomycin', 'glycopeptide'
            ]

        # Fungal
        if 'fungal' in c_lower or 'fungus' in c_lower or 'yeast' in c_lower:
            return ['antifungal', 'azole', 'echinocandin', 'allylamine']

        # Stomach/GERD
        if 'gerd' in c_lower or 'reflux' in c_lower:
            return ['gastroesophageal', 'proton pump inhibitor', 'antacid', 'h2 antagonist']

        if 'stomach' in c_lower or 'gastric' in c_lower:
            return ['antacid', 'proton pump inhibitor', 'h2 antagonist', 'gastric']

        # Hypertension
        if 'hypertension' in c_lower or 'blood pressure' in c_lower:
            if 'asthma' in all_conditions_text or 'copd' in all_conditions_text:
                return ['antihypertensive', 'ace inhibitor', 'calcium channel blocker', 'diuretic', 'angiotensin']
            else:
                return ['antihypertensive', 'ace inhibitor', 'beta blocker', 'calcium channel blocker', 'diuretic']

        # Headache
        if 'headache' in c_lower or 'migraine' in c_lower:
            return ['migraine', 'acetaminophen', 'paracetamol', 'triptan', 'nsaid', 'salicylate']

        # --- GENERIC CATEGORY MAPPINGS ---
        terms = [c_lower]
        if 'pain' in c_lower or 'ache' in c_lower:
            terms.extend(['analgesic', 'antinociceptive', 'nsaid', 'acetaminophen', 'paracetamol'])
        if 'fever' in c_lower:
            terms.extend(['antipyretic', 'pyrexia', 'acetaminophen', 'paracetamol'])
        if 'diabetes' in c_lower:
            terms.extend(['hypoglycemic', 'antidiabetic', 'insulin', 'biguanide', 'sulfonylurea'])
        if 'anxiety' in c_lower:
            terms.extend(['anxiolytic', 'benzodiazepine'])
        if 'insomnia' in c_lower:
            terms.extend(['sedative', 'hypnotic', 'sleep'])
        if 'cholesterol' in c_lower:
            terms.extend(['statin', 'lipid-lowering', 'fibrates'])

        # Added to ensure Mianserin/SSRIs are found correctly
        if 'depression' in c_lower:
            terms.extend(['antidepressant', 'ssri', 'snri', 'tricyclic', 'tetracyclic', 'mao inhibitor'])

        return list(set(terms))

    def _get_route_filter(self, condition):
        c_lower = condition.lower()

        systemic_indicators = [
            'headache', 'back pain', 'fever', 'diabetes', 'hypertension',
            'cholesterol', 'gerd', 'stomach', 'anxiety', 'insomnia',
            'bacterial', 'infection', 'depression'
        ]

        if any(x in c_lower for x in systemic_indicators):
            return "oral"

        if any(x in c_lower for x in ['eye', 'ocular', 'glaucoma']):
            return "ophthalmic"
        if any(x in c_lower for x in ['skin', 'rash', 'dermatitis', 'topical', 'itch', 'fungal']):
            return "topical"
        if 'fungal' in c_lower:
            return ""

        return "oral"

    def _fetch_candidates(self, original_conditions):
        conn = self._get_connection()
        cursor = conn.cursor()
        candidates = set()
        coverage = defaultdict(set)
        drug_info = {}

        all_conditions_text = " ".join(original_conditions).lower()
        print(f"Fetching drugs for conditions: {original_conditions}")

        for cond in original_conditions:
            search_terms = self._get_search_terms(cond, all_conditions_text)
            route_pref = self._get_route_filter(cond)

            likes = " OR ".join(["i.indication_text LIKE ?"] * len(search_terms))
            params = [f'%{term}%' for term in search_terms]

            exclusions = []

            # Cancer Check
            if 'cancer' not in cond.lower() and 'tumor' not in cond.lower() and 'chemo' not in cond.lower():
                exclusions.extend(['cancer', 'carcinoma', 'metastatic', 'chemotherapy', 'palliation'])

            # Anesthetic Check
            if 'pain' in cond.lower() or 'headache' in cond.lower() or 'ache' in cond.lower():
                exclusions.extend(['anesthetic', 'numbing', 'local anesthesia'])

            # 3. ASTHMA / BETA BLOCKER CHECK
            if 'asthma' in all_conditions_text or 'copd' in all_conditions_text:
                exclusions.extend(['beta blocker', 'beta-adrenergic', 'beta-blocker', 'beta antagonist'])

            not_likes_sql = ""
            if exclusions:
                # Checks Indication, MOA, and Description for the banned terms
                not_likes_sql = " AND " + " AND ".join([
                    f"(i.indication_text NOT LIKE ? AND d.moa NOT LIKE ? AND d.description NOT LIKE ?)"
                    for _ in exclusions
                ])
                for ex in exclusions:
                    params.extend([f'%{ex}%', f'%{ex}%', f'%{ex}%'])

            route_sql = ""
            if route_pref:
                route_sql = f"""
                    AND EXISTS (
                        SELECT 1 FROM dosages dos 
                        WHERE dos.drugbank_id = d.drugbank_id 
                        AND dos.route LIKE '%{route_pref}%'
                    )
                """

            query = f"""
                SELECT d.drugbank_id, d.name, t.toxicity_text, p.cost, d.description, d.half_life, d.clearance
                FROM indications i
                JOIN drugs d ON i.drugbank_id = d.drugbank_id
                LEFT JOIN toxicity t ON d.drugbank_id = t.drugbank_id
                LEFT JOIN prices p ON d.drugbank_id = p.drugbank_id
                WHERE ({likes})
                {not_likes_sql}
                AND d.groups LIKE '%approved%'
                AND d.groups NOT LIKE '%vet_approved%'
                AND d.groups NOT LIKE '%withdrawn%'
                {route_sql}
            """

            cursor.execute(query, params)
            rows = cursor.fetchall()

            if not rows:
                print(f"⚠️ No drugs found for: {cond} (terms: {search_terms})")

            for rid, name, tox, price, desc, hl, cl in rows:
                candidates.add(rid)
                coverage[cond].add(rid)

                if rid not in drug_info:
                    hl_val = self._parse_half_life(hl)
                    tox_score = len(tox) if tox else 500
                    safety_score = (tox_score / 10) + (hl_val * 0.5)

                    drug_info[rid] = {
                        'id': rid,
                        'name': name,
                        'description': desc,
                        'toxicity_score': safety_score,
                        'price_val': self._clean_price(price),
                        'half_life': hl_val,
                        'covered_conditions': []
                    }

        conn.close()
        return list(candidates), coverage, drug_info

    def _get_interaction_graph(self, candidates):
        """Direct reported interactions from DB."""
        if not candidates: return set()
        conn = self._get_connection()
        cursor = conn.cursor()
        placeholders = ','.join('?' for _ in candidates)

        query = f'''
            SELECT drugbank_id, target_drug_id 
            FROM interactions 
            WHERE drugbank_id IN ({placeholders}) AND target_drug_id IN ({placeholders})
        '''
        cursor.execute(query, candidates * 2)
        interactions = set()
        for da, db in cursor.fetchall():
            interactions.add(tuple(sorted((da, db))))
        conn.close()
        return interactions

    def _get_enzyme_conflicts(self, candidates):
        """DETECTS METABOLIC CONFLICTS (CYP450 system)."""
        if not candidates: return set()
        conn = self._get_connection()
        cursor = conn.cursor()
        placeholders = ','.join('?' for _ in candidates)

        query = f'''
            SELECT drugbank_id, enzyme_name, action, inhibition_strength, induction_strength
            FROM enzymes
            WHERE drugbank_id IN ({placeholders})
            AND (organism = 'Humans' OR organism IS NULL OR organism = '')
        '''
        cursor.execute(query, candidates)

        enzyme_map = defaultdict(lambda: defaultdict(list))

        for did, enz, action, inhib, induc in cursor.fetchall():
            action_lower = action.lower() if action else ""

            if 'substrate' in action_lower:
                enzyme_map[enz]['substrate'].append(did)
            if 'inhibitor' in action_lower:
                enzyme_map[enz]['inhibitor'].append(did)
            if 'inducer' in action_lower:
                enzyme_map[enz]['inducer'].append(did)

        conflicts = set()

        for enz, roles in enzyme_map.items():
            substrates = roles['substrate']
            inhibitors = roles['inhibitor']
            inducers = roles['inducer']

            # Case 1: Inhibitor + Substrate (Toxicity)
            for sub in substrates:
                for inh in inhibitors:
                    if sub != inh:
                        conflicts.add(tuple(sorted((sub, inh))))

            # Case 2: Inducer + Substrate (Failure)
            for sub in substrates:
                for ind in inducers:
                    if sub != ind:
                        conflicts.add(tuple(sorted((sub, ind))))

        conn.close()
        return conflicts

    def solve_ilp(self, conditions):
        print(f"Starting ILP Optimization for: {conditions}")
        candidates, coverage_map, drug_info = self._fetch_candidates(conditions)

        if not candidates:
            return {"status": "No drugs found", "regimen": [], "total_cost": 0}

        direct_conflicts = self._get_interaction_graph(candidates)
        metabolic_conflicts = self._get_enzyme_conflicts(candidates)
        all_conflicts = direct_conflicts.union(metabolic_conflicts)

        prob = pulp.LpProblem("Drug_Opt", pulp.LpMinimize)
        x = pulp.LpVariable.dicts("drug", candidates, cat='Binary')
        z = pulp.LpVariable.dicts("conflict", list(all_conflicts), cat='Binary')

        # Weights
        W_COUNT = 1000
        W_DIRECT = 500
        W_METABOLIC = 300
        W_SAFETY = 5.0
        W_PRICE = 0.05

        conflict_penalty = 0
        for pair in all_conflicts:
            weight = W_DIRECT if pair in direct_conflicts else W_METABOLIC
            conflict_penalty += weight * z[pair]

        # Objective
        prob += (
                pulp.lpSum([x[i] for i in candidates]) * W_COUNT +
                conflict_penalty +
                pulp.lpSum([x[i] * drug_info[i]['toxicity_score'] for i in candidates]) * W_SAFETY +
                pulp.lpSum([x[i] * drug_info[i]['price_val'] for i in candidates]) * W_PRICE
        )

        # Constraints
        for cond in conditions:
            valid_drugs = coverage_map[cond]
            if valid_drugs:
                prob += pulp.lpSum([x[d] for d in valid_drugs]) >= 1
            else:
                print(f"⚠️ Cannot cover condition: {cond}")

        for (d1, d2) in all_conflicts:
            prob += z[(d1, d2)] >= x[d1] + x[d2] - 1

        prob.solve(pulp.PULP_CBC_CMD(msg=False))

        results = []
        selected = [d for d in candidates if pulp.value(x[d]) == 1.0]

        for d in selected:
            entry = drug_info[d]
            entry['covered_conditions'] = [c for c in conditions if d in coverage_map[c]]
            results.append(entry)

        return {
            "status": "Success",
            "regimen": results,
            "total_cost": sum(r['price_val'] for r in results),
            "conflict_count": sum(pulp.value(z[k]) for k in all_conflicts)
        }

    def solve_greedy(self, conditions):
        print(f"Starting Greedy Optimization for: {conditions}")
        candidates_list, coverage_map, drug_info = self._fetch_candidates(conditions)

        if not candidates_list:
            return {"status": "No drugs found", "regimen": [], "total_cost": 0}

        direct_conflicts = self._get_interaction_graph(candidates_list)
        metabolic_conflicts = self._get_enzyme_conflicts(candidates_list)
        all_conflicts = direct_conflicts.union(metabolic_conflicts)

        conflict_map = defaultdict(set)
        for d1, d2 in all_conflicts:
            conflict_map[d1].add(d2)
            conflict_map[d2].add(d1)

        uncovered = set(conditions)
        selected_drugs = []
        total_conflicts_found = 0

        # Weights
        W_COVER = 1000
        W_CONFLICT = 500
        W_SAFETY = 5.0
        W_PRICE = 0.05

        while uncovered:
            valid_candidates = []
            for d_id in candidates_list:
                can_cover = [c for c in uncovered if d_id in coverage_map[c]]
                if can_cover and d_id not in [s['id'] for s in selected_drugs]:
                    valid_candidates.append(d_id)

            if not valid_candidates:
                break

            best_candidate = None
            best_score = -float('inf')

            for d_id in valid_candidates:
                info = drug_info[d_id]
                new_coverage_count = len([c for c in uncovered if d_id in coverage_map[c]])
                current_conflicts = 0
                for selected in selected_drugs:
                    if selected['id'] in conflict_map[d_id]:
                        current_conflicts += 1

                score = (new_coverage_count * W_COVER) - \
                        (current_conflicts * W_CONFLICT) - \
                        (info['toxicity_score'] * W_SAFETY) - \
                        (info['price_val'] * W_PRICE)

                if score > best_score:
                    best_score = score
                    best_candidate = d_id

            if best_candidate:
                covered_now = [c for c in uncovered if best_candidate in coverage_map[c]]
                for selected in selected_drugs:
                    if selected['id'] in conflict_map[best_candidate]:
                        total_conflicts_found += 1

                drug_entry = drug_info[best_candidate]
                drug_entry['covered_conditions'] = [c for c in conditions if best_candidate in coverage_map[c]]
                selected_drugs.append(drug_entry)

                for c in covered_now:
                    uncovered.remove(c)
            else:
                break

        return {
            "status": "Success (Greedy)",
            "regimen": selected_drugs,
            "total_cost": sum(d['price_val'] for d in selected_drugs),
            "conflict_count": total_conflicts_found
        }