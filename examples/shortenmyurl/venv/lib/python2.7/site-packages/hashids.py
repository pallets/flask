"""Implements the hashids algorithm in python. For more information, visit
http://www.hashids.org/. Compatible with Python 2.5, 2.6, 2.7 and 3.4+"""

from math import ceil

__version__ = '1.0.1'

RATIO_SEPARATORS = 3.5
RATIO_GUARDS = 12

# Python 2/3 compatibility code
try:
    StrType = basestring
except NameError:
    StrType = str


# end of compatibility code
def _is_str(candidate):
    """Returns whether a value is a string."""
    return isinstance(candidate, StrType)


def _is_uint(number):
    """Returns whether a value is an unsigned integer."""
    try:
        return number == int(number) and number >= 0
    except ValueError:
        return False


def _split(string, splitters):
    """Splits a string into parts at multiple characters"""
    part = ''
    for character in string:
        if character in splitters:
            yield part
            part = ''
        else:
            part += character
    yield part


def _hash(number, alphabet):
    """Hashes `number` using the given `alphabet` sequence."""
    hashed = ''
    len_alphabet = len(alphabet)
    while True:
        hashed = alphabet[number % len_alphabet] + hashed
        number //= len_alphabet
        if not number:
            return hashed


def _unhash(hashed, alphabet):
    """Restores a number tuple from hashed using the given `alphabet` index."""
    number = 0
    len_hash = len(hashed)
    len_alphabet = len(alphabet)
    for i, character in enumerate(hashed):
        position = alphabet.index(character)
        number += position * len_alphabet ** (len_hash - i - 1)

    return number


def _reorder(string, salt):
    """Reorders `string` according to `salt`."""
    len_salt = len(salt)

    if len_salt == 0:
        return string

    i, index, integer_sum = len(string) - 1, 0, 0
    while i > 0:
        index %= len_salt
        integer = ord(salt[index])
        integer_sum += integer
        j = (integer + index + integer_sum) % i

        temp = string[j]
        trailer = string[j+1:] if j + 1 < len(string) else ''
        string = string[0:j] + string[i] + trailer
        string = string[0:i] + temp + string[i+1:]

        i -= 1
        index += 1

    return string


def _index_from_ratio(dividend, divisor):
    """Returns the ceiled ratio of two numbers as int."""
    return int(ceil(float(dividend) / divisor))


def _ensure_length(encoded, min_length, alphabet, guards, values_hash):
    """Ensures the minimal hash length"""
    len_guards = len(guards)
    guard_index = (values_hash + ord(encoded[0])) % len_guards
    encoded = guards[guard_index] + encoded

    if len(encoded) < min_length:
        guard_index = (values_hash + ord(encoded[2])) % len_guards
        encoded += guards[guard_index]

    split_at = len(alphabet) // 2
    while len(encoded) < min_length:
        alphabet = _reorder(alphabet, alphabet)
        encoded = alphabet[split_at:] + encoded + alphabet[:split_at]
        excess = len(encoded) - min_length
        if excess > 0:
            from_index = excess // 2
            encoded = encoded[from_index:from_index+min_length]

    return encoded


def _encrypt(values, salt, min_length, alphabet, separators, guards):
    """Helper function that does the hash building without argument checks."""

    len_alphabet = len(alphabet)
    len_separators = len(separators)
    values_hash = sum(x % (i + 100) for i, x in enumerate(values))
    encoded = lottery = alphabet[values_hash % len(alphabet)]

    last = None
    for i, value in enumerate(values):
        alphabet_salt = (lottery + salt + alphabet)[:len_alphabet]
        alphabet = _reorder(alphabet, alphabet_salt)
        last = _hash(value, alphabet)
        encoded += last
        value %= ord(last[0]) + i
        encoded += separators[value % len_separators]

    encoded = encoded[:-1]  # cut off last separator

    return (encoded if len(encoded) >= min_length else
            _ensure_length(encoded, min_length, alphabet, guards, values_hash))


def _decrypt(hashid, salt, alphabet, separators, guards):
    """Helper method that restores the values encoded in a hashid without
    argument checks."""
    parts = tuple(_split(hashid, guards))
    hashid = parts[1] if 2 <= len(parts) <= 3 else parts[0]

    if not hashid:
        return

    lottery_char = hashid[0]
    hashid = hashid[1:]

    hash_parts = _split(hashid, separators)
    for part in hash_parts:
        alphabet_salt = (lottery_char + salt + alphabet)[:len(alphabet)]
        alphabet = _reorder(alphabet, alphabet_salt)
        yield _unhash(part, alphabet)


class Hashids(object):
    """Hashes and restores values using the "hashids" algorithm."""
    ALPHABET = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'

    def __init__(self, salt='', min_length=0, alphabet=ALPHABET):
        """
        Initializes a Hashids object with salt, minimum length, and alphabet.

        :param salt: A string influencing the generated hash ids.
        :param min_length: The minimum length for generated hashes
        :param alphabet: The characters to use for the generated hash ids.
        """
        self._min_length = max(int(min_length), 0)
        self._salt = salt

        separators = ''.join(x for x in 'cfhistuCFHISTU' if x in alphabet)
        alphabet = ''.join(x for i, x in enumerate(alphabet)
                           if alphabet.index(x) == i and x not in separators)

        len_alphabet, len_separators = len(alphabet), len(separators)
        if len_alphabet + len_separators < 16:
            raise ValueError('Alphabet must contain at least 16 '
                             'unique characters.')

        separators = _reorder(separators, salt)

        min_separators = _index_from_ratio(len_alphabet, RATIO_SEPARATORS)
        if not separators or len_separators < min_separators:
            if min_separators == 1:
                min_separators = 2
            if min_separators > len_separators:
                split_at = min_separators - len_separators
                separators += alphabet[:split_at]
                alphabet = alphabet[split_at:]
                len_alphabet = len(alphabet)

        alphabet = _reorder(alphabet, salt)
        num_guards = _index_from_ratio(len_alphabet, RATIO_GUARDS)
        if len_alphabet < 3:
            guards = separators[:num_guards]
            separators = separators[num_guards:]
        else:
            guards = alphabet[:num_guards]
            alphabet = alphabet[num_guards:]

        self._alphabet = alphabet
        self._guards = guards
        self._separators = separators

    def encrypt(self, *values):
        """Builds a hash from the passed `values`.

        :param values The values to transform into a hashid

        >>> hashids = Hashids('arbitrary salt', 16, 'abcdefghijkl0123456')
        >>> hashids.encrypt(1, 23, 456)
        '1d6216i30h53elk3'
        """
        if not (values and all(_is_uint(x) for x in values)):
            return ''

        return _encrypt(values, self._salt, self._min_length, self._alphabet,
                        self._separators, self._guards)

    def decrypt(self, hashid):
        """Restore a tuple of numbers from the passed `hashid`.

        :param hashid The hashid to decrypt

        >>> hashids = Hashids('arbitrary salt', 16, 'abcdefghijkl0123456')
        >>> hashids.decrypt('1d6216i30h53elk3')
        (1, 23, 456)
        """
        if not hashid or not _is_str(hashid):
            return ()
        try:
            numbers = tuple(_decrypt(hashid, self._salt, self._alphabet,
                                     self._separators, self._guards))

            return numbers if hashid == self.encrypt(*numbers) else ()
        except ValueError:
            return ()
