#!/usr/bin/env python3
"""Audit author-year citations and bind the checks to exact DOCX bytes.

Usage: python revision_checks/check_final_citations.py --main MAIN.docx --supplementary SI.docx
Optional: --blind-main BLIND_MAIN.docx --blind-supplementary BLIND_SI.docx
This uses the standard library and does not alter the documents.
"""
import argparse
import collections
import datetime
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main', 'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
TEXT_TAGS = {'{' + uri + '}t' for uri in NS.values()}

def node_text(node):
    return ''.join(t.text or '' for t in node.iter() if t.tag in TEXT_TAGS)
YEAR = r'(?:19|20)\d{2}[a-z]?'
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def inspect_docx(path):
    path = Path(path)
    with zipfile.ZipFile(path) as archive:
        xml = ET.fromstring(archive.read('word/document.xml'))
        rel_xml = ET.fromstring(archive.read('word/_rels/document.xml.rels'))
    paragraphs = [
        node_text(p)
        for p in xml.findall('./w:body/w:p', NS)
    ]
    tables = [
        node_text(p)
        for p in xml.findall('./w:body/w:tbl//w:p', NS)
    ]
    relationships = {r.get('Id'): r.get('Target') for r in rel_xml}
    hyperlinks = []
    for h in xml.findall('.//w:hyperlink', NS):
        text = ''.join(t.text or '' for t in h.findall('.//w:t', NS))
        hyperlinks.append({'label': text, 'target': relationships.get(h.get(REL))})
    return {
        'file': path.name,
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'paragraphs': paragraphs,
        'tables': tables,
        'hyperlinks': hyperlinks,
    }


def reference_records(paragraphs):
    boundary = paragraphs.index('References')
    entries = []
    for text in paragraphs[boundary + 1:]:
        if not text.strip():
            continue
        # Submission layouts may place tables/captions after the bibliography.
        if re.match(r'^(?:Table|Figure)\s+\d+\.', text):
            break
        year = re.search(r'\((' + YEAR + r')\)', text)
        if not year:
            raise ValueError('Reference without an author-year key: ' + text)
        author_block = text[:year.start()].strip().rstrip('.')
        first = author_block.split(',')[0]
        aliases = [first]
        if first == 'International Capital Market Association':
            aliases.append('ICMA')
        entries.append({
            'key': first + ' ' + year.group(1),
            'first_author': first,
            'year': year.group(1),
            'aliases': aliases,
            'author_surnames': [part.strip().removeprefix('& ').strip() for part in author_block.split(',')[::2]],
            'reference': text,
            'doi': re.findall(r'https://doi\.org/(\S+)', text),
        })
    return boundary, entries


def scan_citations(texts, references):
    occurrences = collections.defaultdict(list)
    year_contexts = []
    for paragraph, text in enumerate(texts, 1):
        year_spans = list(re.finditer(r'\b' + YEAR + r'\b', text))
        for year in year_spans:
            prior = text[max(0, year.start() - 190):year.start()]
            # Citation syntax has a parenthesized or comma-separated year. Dates
            # and analytical observation windows are separately retained below.
            citation_syntax = bool(re.search(r'(?:,|\()\s*$', prior))
            matches = []
            author_strings = {}
            if citation_syntax:
                for ref in references:
                    if ref['year'] != year.group():
                        continue
                    for alias in ref['aliases']:
                        hits = list(re.finditer(r'(?<![\w-])' + re.escape(alias) + r'(?![\w-])', prior))
                        for hit in hits:
                            tail = prior[hit.end():]
                            # Cross neither another year nor a semicolon nor a
                            # sentence boundary; allow et al. and possessives.
                            simple = tail.replace('et al.', 'et al')
                            if re.search(r'\b' + YEAR + r'\b|;|[.!?]', simple):
                                continue
                            if len(tail) <= 145:
                                matches.append(ref['key'])
                                author_strings[ref['key']] = prior[hit.start():].strip().rstrip(' (,' )
                                break
                        if ref['key'] in matches:
                            break
            matches = sorted(set(matches))
            context = text[max(0, year.start() - 155):min(len(text), year.end() + 70)]
            record = {'paragraph': paragraph, 'year': year.group(), 'context': context,
                      'matching_reference_keys': matches, 'citation_syntax': citation_syntax,
                      'author_strings': author_strings}
            year_contexts.append(record)
            for key in matches:
                occurrences[key].append({'paragraph': paragraph, 'context': context, 'author_string': author_strings[key]})
    return occurrences, year_contexts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--main', required=True)
    parser.add_argument('--supplementary', required=True)
    parser.add_argument('--blind-main')
    parser.add_argument('--blind-supplementary')
    parser.add_argument('--output', default=str(Path(__file__).with_name('final_citation_check.json')))
    parser.add_argument('--review-context-output', help='Optional detailed review context; not needed for public validation.')
    args = parser.parse_args()
    main_doc = inspect_docx(args.main)
    si = inspect_docx(args.supplementary)
    boundary, references = reference_records(main_doc['paragraphs'])
    body = main_doc['paragraphs'][:boundary] + main_doc['tables']
    occurrences, year_contexts = scan_citations(body, references)
    si_occurrences, si_year_contexts = scan_citations(si['paragraphs'] + si['tables'], references)
    author_spelling_or_order_flags = []
    for ref in references:
        for occurrence in occurrences.get(ref['key'], []):
            actual = occurrence['author_string'].replace('’s', '').replace("'s", '')
            actual = re.sub(r'\s*\[ICMA\]', '', actual)
            if 'et al.' in actual:
                expected = ref['first_author'] + ' et al.'
                if actual != expected:
                    author_spelling_or_order_flags.append({'key': ref['key'], 'paragraph': occurrence['paragraph'], 'actual': actual, 'expected': expected})
            elif actual == 'ICMA':
                pass
            else:
                names = [n.strip() for n in re.split(r',\s*|\s+(?:and|&)\s+', actual) if n.strip()]
                names = [n.removeprefix('& ').removeprefix('and ').strip() for n in names]
                if names != ref['author_surnames']:
                    author_spelling_or_order_flags.append({'key': ref['key'], 'paragraph': occurrence['paragraph'], 'actual': names, 'expected': ref['author_surnames']})
        ref['main_occurrences'] = [{'paragraph': o['paragraph']} for o in occurrences.get(ref['key'], [])]
        ref['supplementary_occurrences'] = [{'paragraph': o['paragraph']} for o in si_occurrences.get(ref['key'], [])]
    duplicates = [key for key, count in collections.Counter(r['key'] for r in references).items() if count > 1]
    duplicate_dois = [doi for doi, count in collections.Counter(d for r in references for d in r['doi']).items() if count > 1]
    unresolved = [r for r in year_contexts if r['citation_syntax'] and not r['matching_reference_keys']]
    ambiguous = [r for r in year_contexts if len(r['matching_reference_keys']) > 1]
    url_mismatches = [h for h in main_doc['hyperlinks'] if h['label'].startswith('https://doi.org/') and h['label'] != h['target']]
    abstract = main_doc['paragraphs'][main_doc['paragraphs'].index('Abstract') + 1]
    keywords = next(p for p in main_doc['paragraphs'] if p.startswith('Keywords:'))
    uncited = [r['key'] for r in references if not r['main_occurrences']]
    result = {
        'version': '2026-10-11-r4',
        'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'file': main_doc['file'], 'sha256': main_doc['sha256'],
        'method': 'Extract actual DOCX XML; map bounded author-year citation syntax to the final bibliography; retain all year contexts for review. Check duplicate keys/DOIs and visible DOI hyperlink targets. No document changes.',
        'reference_count': len(references), 'references_cited': len(references) - len(uncited),
        'uncited_references': uncited, 'duplicate_reference_keys': duplicates,
        'duplicate_dois': duplicate_dois, 'unresolved_main_citation_candidates': unresolved,
        'ambiguous_main_citation_candidates': ambiguous, 'doi_hyperlink_mismatches': url_mismatches,
        'author_spelling_or_order_flags': author_spelling_or_order_flags,
        'abstract_words_whitespace': len(abstract.split()),
        'abstract_words_punctuation_split': len(re.findall(r"\b[\w]+(?:[’'][\w]+)*\b", abstract)),
        'word_count_method': 'Whitespace tokens after joining distinct Word paragraphs with spaces, including table-cell paragraphs and editable equation text; pre-References body includes title, abstract, keywords and captions.',
        'keyword_count': len(keywords.split(':', 1)[1].split(';')),
        'main_words_including_tables_captions_and_math_excluding_references_whitespace': len(' '.join(body).split()),
        'main_words_including_tables_math_and_references_whitespace': len(' '.join(main_doc['paragraphs'] + main_doc['tables']).split()),
        'supplementary_check': {'file': si['file'], 'sha256': si['sha256'], 'references_cited': sorted(si_occurrences)},
        'references': references,
        'year_scan_coverage': {'main_year_occurrences': len(year_contexts), 'main_citation_syntax_occurrences': sum(y['citation_syntax'] for y in year_contexts), 'supplementary_year_occurrences': len(si_year_contexts)},
        'limits': 'Internal citation consistency is distinct from live metadata, source interpretation, journal classification, and human independent verification. Year-only dates can appear among candidates and must be reviewed rather than asserted to be citations.',
    }
    result['automated_passed'] = not (uncited or duplicates or duplicate_dois or ambiguous or url_mismatches or unresolved or author_spelling_or_order_flags)
    result['associated_blinded_documents'] = []
    for role, path in [('blind_main', args.blind_main), ('blind_supplementary', args.blind_supplementary)]:
        if path:
            doc = inspect_docx(path)
            result['associated_blinded_documents'].append({'role': role, 'file': doc['file'], 'sha256': doc['sha256']})
            if role == 'blind_main':
                _, blind_refs = reference_records(doc['paragraphs'])
                result['blinded_main_references_identical'] = [r['reference'] for r in references] == [r['reference'] for r in blind_refs]
                result['automated_passed'] = result['automated_passed'] and result['blinded_main_references_identical']
    if args.review_context_output:
        Path(args.review_context_output).write_text(json.dumps({'main': year_contexts, 'supplementary': si_year_contexts}, ensure_ascii=False, indent=2) + '\n')
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ['references', 'main_year_contexts', 'supplementary_year_contexts']}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['automated_passed'] else 1)


if __name__ == '__main__':
    main()
