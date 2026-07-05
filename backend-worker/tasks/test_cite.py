import json, sys

csl_map = {
    'Karmakar2021': {
        'id': 'Karmakar2021',
        'type': 'article-journal',
        'author': [{'family': 'Karmakar', 'given': 'A'}],
        'title': 'IoT Security',
        'issued': {'date-parts': [[2021]]}
    }
}

def format_author_year_inline(keys, csl_map, style='apa'):
    parts = []
    for k in keys:
        entry = csl_map.get(k)
        if not entry:
            parts.append(k)
            continue
        authors = entry.get('author', [])
        year = ''
        issued = entry.get('issued', {})
        if issued:
            dp = issued.get('date-parts', [])
            if dp and dp[0]:
                year = str(dp[0][0])
        if not authors:
            parts.append('(' + year + ')' if year else k)
            continue
        family = authors[0].get('family', '')
        if style == 'mla':
            parts.append(family if family else k)
        elif style == 'chicago':
            parts.append(family + ' ' + year if family and year else k)
        else:
            parts.append(family + ', ' + year if family and year else k)
    if not parts:
        return ''
    if style == 'mla':
        return '(' + ' ,'.join(parts) + ')'
    return '(' + ' ; '.join(parts) + ')'

# Test single citation
result = format_author_year_inline(['Karmakar2021'], csl_map, 'apa')
print('Single APA:', result)
assert result == '(Karmakar, 2021)', 'Expected (Karmakar, 2021), got ' + result

# Test multiple citations
csl_map['He2022'] = {
    'id': 'He2022',
    'author': [{'family': 'He', 'given': 'X'}],
    'issued': {'date-parts': [[2022]]}
}
csl_map['NIST2020'] = {
    'id': 'NIST2020',
    'author': [{'family': 'National Institute of Standards and Technology', 'given': ''}],
    'issued': {'date-parts': [[2020]]}
}

result = format_author_year_inline(['NIST2020', 'He2022'], csl_map, 'apa')
print('Multi APA:', result)
assert ';' in result, 'Expected semicolon separator'

result = format_author_year_inline(['Karmakar2021'], csl_map, 'chicago')
print('Chicago:', result)
assert result == '(Karmakar 2021)', 'Expected (Karmakar 2021), got ' + result

result = format_author_year_inline(['Karmakar2021'], csl_map, 'mla')
print('MLA:', result)
assert result == '(Karmakar)', 'Expected (Karmakar), got ' + result

# Test multiple keys APA
result = format_author_year_inline(['Karmakar2021', 'He2022'], csl_map, 'apa')
print('Multi-key APA:', result)
assert ';' in result

print('All tests passed!')
