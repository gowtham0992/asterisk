"""Describe revision changes without attributing performance or causation."""
import hashlib

CONTRACT_FIELDS = ('split_file', 'sample_column', 'partition_column', 'mapping_file',
                   'mapping_sample_column', 'entity_column', 'train_values', 'test_values')


def selected_rule(audit):
    return audit.get('reviewed_rule') or (audit.get('proposal') or {}).get('rule')


def compare(parent, child):
    previous, current = selected_rule(parent), selected_rule(child)
    rule_changes = []
    for field in ('unit', *CONTRACT_FIELDS, 'citations'):
        before, after = (previous or {}).get(field), (current or {}).get(field)
        if field in ('train_values','test_values'):
            before = sorted(before) if before is not None else None
            after = sorted(after) if after is not None else None
        if before != after:
            rule_changes.append({'field':field,'before':before,'after':after})
    def fingerprints(audit):
        return {f['name']:hashlib.sha256(f['content'].encode()).hexdigest() for f in audit['input']['files']}
    left, right = fingerprints(parent), fingerprints(child)
    files = [{'name':name,'change':'added' if name not in left else 'removed' if name not in right else 'unchanged' if left[name]==right[name] else 'modified',
              'before_sha256':left.get(name),'after_sha256':right.get(name)} for name in sorted(left.keys() | right.keys())]
    metrics = [{'field':field,'before':(parent.get('result') or {}).get(field),'after':(child.get('result') or {}).get(field)}
               for field in ('status','shared_entities','affected_test_rows','test_rows','mapping_coverage_percent','missing_count')]
    return {'parent':{'id':parent['id'],'title':parent['input']['title'],'state':parent['state']},
            'child':{'id':child['id'],'title':child['input']['title'],'state':child['state']},
            'claim':{'before':parent['input']['claim'],'after':child['input']['claim']},
            'rule_changes':rule_changes, 'files':files, 'metrics':metrics,
            'contract_changed':bool(previous and current and any(c['field'] in CONTRACT_FIELDS for c in rule_changes)),
            'rule_status':'added' if previous is None and current is not None else 'removed' if previous is not None and current is None else 'changed' if rule_changes else 'unchanged',
            'both_complete':parent['state']=='complete' and child['state']=='complete'}
