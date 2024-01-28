import hashlib
import random
import string
import uuid
from flask_babel import gettext

# required answerer attribute
# specifies which search query keywords triggers this answerer
keywords = ('random', 'rand', '!r')

random_int_max = 2**31
random_string_letters = string.ascii_lowercase + string.digits + string.ascii_uppercase


def random_characters():
    return [random.choice(random_string_letters) for _ in range(random.randint(8, 32))]


def random_string():
    return ''.join(random_characters())


def random_float():
    return str(random.random())


def random_int():
    return str(random.randint(-random_int_max, random_int_max))


def random_sha256():
    m = hashlib.sha256()
    m.update(''.join(random_characters()).encode())
    return str(m.hexdigest())


def random_uuid():
    return str(uuid.uuid4())


def random_color():
    color = "%06x" % random.randint(0, 0xFFFFFF)
    return f"#{color.upper()}"

def random_coin():
    return random.choice(['heads', 'tails'])

def random_card():
    return random.choice(['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']) + ' of ' + random.choice(['diamonds', 'spades', 'hearts', 'clubs'])

def random_dice():
    return str(random.randint(1, 6))

def random_d20():
    return str(random.randint(1, 20))

def random_number(x: int):
    return str(random.randint(1, x))

def random_groups(team_count: int, items: list):
    if type(items) is list and len(items) < 2:
        if ',' in items[0]:
            items = items[0].split(',')
        else:
            return []

    random.shuffle(items)
    groups = [[] for _ in range(team_count)]

    for i in range(len(items)):
        groups[i % team_count].append(items[i])

    return str(groups).replace("'", "")

random_types = {
    'string': random_string,
    'int': random_int,
    'float': random_float,
    'sha256': random_sha256,
    'uuid': random_uuid,
    'color': random_color,
    'coin': random_coin,
    'card': random_card,
    'dice': random_dice,
    'd20': random_d20,
}


# required answerer function
# can return a list of results (any result type) for a given query
def answer(query):
    parts = query.query.split()
    if len(parts) >= 4:
        if parts[1] == 'groups':
            return [{'answer': random_groups(int(parts[2]), parts[3:])}]
    if len(parts) != 2:
        return []

    if parts[1] not in random_types:
        try:
            if parts[1].isnumeric():
                return [{'answer': random_number(int(parts[1]))}]
        except:
            pass
        return []

    return [{'answer': random_types[parts[1]]()}]


# required answerer function
# returns information about the answerer
def self_info():
    return {
        'name': gettext('Random value generator'),
        'description': gettext('Generate different random values'),
        'examples': ['random {}'.format(x) for x in random_types],
    }
