from relation import Relation
from wikidata.utils import get_label
from query import Query


class Fact:

    def __init__(self, subject_id, relation, target_id, use_labels=False):
        self._subject_id = subject_id
        self._relation = relation
        self._target_id = target_id
        self._use_labels = use_labels

    def get_subject_label(self):
        return get_label(self._subject_id)

    def get_target_label(self):
        return get_label(self._target_id)

    def get_relation_label(self):
        return self._relation.name.replace('_', ' ')

    def get_fact_query(self):
        return Query(self._subject_id, self._relation, self._target_id, use_labels=self._use_labels)

    def get_fact_prompt(self):
        return self._relation.phrase(get_label(self._subject_id))

    def get_fact_phrased(self):
        return self._relation.phrase(get_label(self._subject_id)) + f' {get_label(self._target_id)}.'

    def to_dict(self):
        return {
            'prompt': self.get_fact_phrased(),
            'subject_id': self._subject_id,
            'relation': self._relation.name,
            'target_id': self._target_id,
            'use_labels': self._use_labels
        }

    @staticmethod
    def from_dict(d, use_labels=False):
        # Use the use_labels parameter passed in, or get it from the dict if available
        use_labels_value = d.get('use_labels', use_labels)
        return Fact(d['subject_id'], Relation[d['relation']], d['target_id'], use_labels_value)

    def __str__(self):
        return f'({self.get_subject_label()}, {self.get_relation_label()}, {self.get_target_label()})'

