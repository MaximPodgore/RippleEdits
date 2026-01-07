import json
import csv
import os
import functools
from collections import defaultdict
from qwikidata.linked_data_interface import get_entity_dict_from_api
from qwikidata.entity import WikidataItem
from qwikidata.sparql import return_sparql_query_results
import zipfile
import requests


def load_json(path: str):
    with open(path, 'r+', encoding='utf-8') as f:
        result = json.load(f)
    return result


def write_json(d: dict, path: str):
    with open(path, 'w+', encoding='utf-8') as f:
        json.dump(d, f)


def add_to_json(d, path):
    with open(path, 'r+', encoding='utf-8') as f:
        curr_data = json.load(f)
    if isinstance(curr_data, list):
        new_data = curr_data + d
    elif isinstance(curr_data, dict):
        curr_data.update(d)
    with open(path, 'w+', encoding='utf-8') as f:
        json.dump(new_data, f)


def write_to_csv(path: str, table: list):
    with open(path, 'a+', encoding='utf-8') as f:
        csv_writer = csv.writer(f)
        for line in table:
            csv_writer.writerow(line)


def read_from_csv(path: str):
    table = []
    with open(path, 'r+', encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        for line in csv_reader:
            table.append(line)
    return table


def retrieve_from_wikidata(ent: str, wikidata_dir: str = './wikidata_full_kg/filtered_relations'):
    if not ent:
        return None
    relevant_files = []
    for file in os.listdir(wikidata_dir):
        if file[-5:] == '.json':
            relevant_files.append(os.path.join(wikidata_dir, file))

    for path in relevant_files:
        curr_part = load_json(path)
        if ent in curr_part:
            return curr_part[ent]
    return None


def facts_list_to_relation2targets(facts: list):
    relation2targets = defaultdict(list)
    for relation, target in facts:
        relation2targets[relation].append(target)
    return relation2targets


@functools.lru_cache()
def wikidata_item_given_id(ent_id: str):
    try:
        return WikidataItem(get_entity_dict_from_api(ent_id))
    except Exception as e:
        print(f"Failed to fetch Wikidata item for {ent_id}: {e}")
        return None


def get_label(ent_id: str):
    if isinstance(ent_id, list):
        if len(ent_id) > 0:
            ent_id = ent_id[0]
        else:
            return ent_id
    if ent_id[0] != 'Q':
        return ent_id
    # Try local offline mapping first
    local_label = ent_id2label_dict.get(ent_id)
    if local_label:
        return local_label
    # Use direct Wikidata HTTP API with proper User-Agent (old lib method was failing )
    label = _fetch_label_via_http(ent_id)
    if label is not None:
        print(f"Fetched label via HTTP for {ent_id}: {label}")
        return label

    return ent_id


def _fetch_label_via_http(ent_id: str, lang: str = "en"):
    try:
        url = f"https://www.wikidata.org/wiki/Special:EntityData/{ent_id}.json"
        headers = {
            "User-Agent": "RippleEdits/0.1 (https://github.com/edenbiran/RippleEdits)"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"Fallback label fetch failed for {ent_id}: {resp.status_code} {resp.text[:200]}")
            return None
        data = resp.json()
        entity = data.get("entities", {}).get(ent_id, {})
        labels = entity.get("labels", {})
        if lang in labels and "value" in labels[lang]:
            return labels[lang]["value"]
        # If preferred language not present, return any available label
        for entry in labels.values():
            val = entry.get("value")
            if val:
                return val
        return None
    except Exception as e:
        print(f"Fallback label fetch error for {ent_id}: {e}")
        return None


def get_aliases(ent_id: str):
    # Prefer direct HTTP fetch with a proper User-Agent to avoid 403
    aliases = _fetch_aliases_via_http(ent_id)
    if aliases is not None and len(aliases) > 0:
        return aliases
    # Fallback to qwikidata if HTTP fails
    item = wikidata_item_given_id(ent_id)
    if item is not None:
        try:
            return item.get_aliases()
        except Exception:
            pass
    return [ent_id]


def _fetch_aliases_via_http(ent_id: str, lang: str = "en"):
    try:
        if not isinstance(ent_id, str) or not ent_id.startswith("Q"):
            return []
        url = f"https://www.wikidata.org/wiki/Special:EntityData/{ent_id}.json"
        headers = {
            "User-Agent": "RippleEdits/0.1 (https://github.com/edenbiran/RippleEdits)"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            # Non-200; let caller try fallback
            return None
        data = resp.json()
        entity = data.get("entities", {}).get(ent_id, {})
        aliases_by_lang = entity.get("aliases", {})
        results = []
        if lang in aliases_by_lang:
            for entry in aliases_by_lang[lang]:
                val = entry.get("value")
                if val:
                    results.append(val)
        # If no aliases for preferred language, collect any available
        if not results:
            for lang_entries in aliases_by_lang.values():
                for entry in lang_entries:
                    val = entry.get("value")
                    if val:
                        results.append(val)
        return results or None
    except Exception:
        return None


def get_description(ent_id: str):
    item = wikidata_item_given_id(ent_id)
    if item is not None:
        return item.get_description()
    return [ent_id]


def get_targets_given_item_and_relation(item: WikidataItem, relation_id: str):
    related_claims = item.get_truthy_claim_groups()
    if relation_id not in related_claims:
        return []
    curr_relation_claims = related_claims[relation_id]
    try:
        target_ids = [claim.mainsnak.datavalue.value["id"] for claim in curr_relation_claims]
        return target_ids
    except:
        return []


def is_relation_associated(ent_id, relation_id):
    try:
        ent_item = wikidata_item_given_id(ent_id)
    except:
        return False
    return len(get_targets_given_item_and_relation(ent_item, relation_id)) > 0


def is_relations_associated(ent_id, relation_ids: list):
    try:
        ent_item = wikidata_item_given_id(ent_id)
    except:
        return False
    related_claims = ent_item.get_truthy_claim_groups()
    for relation_id in relation_ids:
        if relation_id in related_claims:
            return True
    return False


def subject_relation_to_targets(subject_id: str, relation):
    if not isinstance(relation, str):
        relation_id = relation.id()
    else:
        relation_id = relation
    subject_item = wikidata_item_given_id(subject_id)
    return get_targets_given_item_and_relation(subject_item, relation_id)


def ent_to_relation_ids(ent_id: str):
    item = wikidata_item_given_id(ent_id)
    if item is None:
        return []
    related_claims = item.get_truthy_claim_groups()
    return list(related_claims.keys())


with zipfile.ZipFile('./wikidata/ent_label2id.json.zip', 'r') as zip_ref:
    zip_ref.extractall('./wikidata/')

ent_label2id_dict = load_json('./wikidata/ent_label2id.json')

# Build id->label dictionary for offline fallback
ent_id2label_dict = {}
for label, qid in ent_label2id_dict.items():
    if qid not in ent_id2label_dict:
        ent_id2label_dict[qid] = label


def ent_label2id(label: str):
    if label not in ent_label2id_dict:
        return None
    return ent_label2id_dict[label]


def extract_ent_id_from_url(url: str):
    pointer = len(url) - 1
    while url[pointer] != '/':
        pointer -= 1
    return url[pointer+1:]


def sparkql_res_to_list_of_facts(sparkql_res: dict, relation_id: str):
    resulted_facts = []
    for returned_fact in sparkql_res['results']['bindings']:
        subject, target = returned_fact['item'], returned_fact['target']

        # handling subject
        if subject['type'] == 'uri':
            subject = extract_ent_id_from_url(subject['value'])
        elif subject['type'] == 'literal':
            subject = subject['value']

        # handling target
        if target['type'] == 'uri':
            target = extract_ent_id_from_url(target['value'])
        elif target['type'] == 'literal':
            target = target['value']

        resulted_facts.append((subject, relation_id, target))

    return resulted_facts


def sparkql_res_to_list_of_entities(sparkql_res: dict):
    resulted_entities = []
    for returned_ent in sparkql_res['results']['bindings']:
        subject = returned_ent['itemLabel']

        # handling subject
        if subject['type'] == 'uri':
            subject = extract_ent_id_from_url(subject['value'])
        elif subject['type'] == 'literal':
            subject = subject['value']

        resulted_entities.append(subject)

    return resulted_entities


def subjects_given_relation_target(relation_id: str, target_id: str, limit: int = 10):
    sparql_query = f"""
    SELECT DISTINCT ?item ?itemLabel 
    WHERE
    {{
      ?item wdt:{relation_id} wd:{target_id};
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE]". }}
    }}
    LIMIT {limit}
    """

    try:
        res = return_sparql_query_results(sparql_query)
        return sparkql_res_to_list_of_entities(res)
    except:
        return []

