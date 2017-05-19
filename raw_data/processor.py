

def read_shuttles_clicks():
    with open('db/shuttles_clicks.txt', 'r') as f:
        for _line in f:
            yield _line


# TODO: it's temporary, just for determining what format the data in "shuttles_clicks" has
if __name__ == '__main__':

    possible_values = {
        "collection_name": set(),
        "key": set(),
        "new_value": set()
    }
    for action in read_shuttles_clicks():
        fields = action.split(' | ')

        for field in fields:
            k, v = field.split(' = ')
            if k not in ('dt', 'filter_options') and not str(v).startswith('['):
                possible_values[k].add(v)

    print(possible_values)