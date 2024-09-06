def get_score_for_position(position):
    if position == '':
        return 0
    elif position == 1:
        return 30
    elif position == 2:
        return 20
    elif position == 3:
        return 18
    elif position == 4:
        return 16
    elif position == 5:
        return 14
    elif position == 6:
        return 12
    elif position == 7:
        return 10
    elif position == 8:
        return 9
    elif position == 9:
        return 8
    elif position == 10:
        return 7
    elif position <= 15:
        return 6
    elif position <= 20:
        return 5
    elif position <= 25:
        return 4
    elif position <= 30:
        return 3
    elif position <= 40:
        return 2
    elif position <= 50:
        return 1
    else:
        return 0

def calculate_score(row):
    return sum([
        30 * row['Ace'],
        20 * row['Albatross'],
        8 * row['Eagle'],
        3 * row['Birdie'],
        0.5 * row['Par'],
        -0.5 * row['Bogey'],
        -2 * row['Double Bogey'],
        -5 * row['Triple+ Bogey'],
        get_score_for_position(row['Position'])
    ])

def make_clickable(val):
    return '<a href="{}">{}</a>'.format(val,val)
