'''
    Takes an array of rows as input and prints then as a table.
    Each row should be a dict and the keys are used as the header.
'''

def print_data(data, headers_to_print = None):
    if headers_to_print:
        headers = headers_to_print
    else:
        headers = set()
        for row in data:
            headers = headers | set(row.keys())

    headers = [[header, len(header)] for header in headers]

    for row in data:
        for header in headers:
            _ = row.get(header[0], '')
            if type(_) in [int, float]:
                row[header[0]] = "{:,}".format(_)
            else:
                row[header[0]] = _
            header[1] = max(header[1], len(str(row[header[0]])))

    print_format = (u'{{:>{}}}' * len(headers)).format(*[h[1]+2 for h in headers])
    print(print_format.format(*[h[0] for h in headers]))
    print(print_format.format(*['-'*len(h[0]) for h in headers]))
    for row in data:
        print(print_format.format(*[row.get(h[0], '') for h in headers]))
