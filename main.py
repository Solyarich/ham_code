from typing import List
from math import log2, ceil
from random import randrange
import codecs

all_errors = 0
errors_add = 0
mass_errors = 0
cor_del = 0

crc32 = '100000100110000010001110110110111'

def text_to_bits(text, encoding='utf-8', errors='surrogatepass'):
    bits = bin(int.from_bytes(text.encode(encoding, errors), 'big'))[2:]
    return bits.zfill(8 * ((len(bits) + 7) // 8))

def crc_remainder(input_bitstring, polynomial_bitstring, initial_filler):
    polynomial_bitstring = polynomial_bitstring.lstrip('0')
    len_input = len(input_bitstring)
    initial_padding = (len(polynomial_bitstring) - 1) * initial_filler
    input_padded_array = list(input_bitstring + initial_padding)
    while '1' in input_padded_array[:len_input]:
        cur_shift = input_padded_array.index('1')
        for i in range(len(polynomial_bitstring)):
            input_padded_array[cur_shift + i] \
            = str(int(polynomial_bitstring[i] != input_padded_array[cur_shift + i]))
    return ''.join(input_padded_array)[len_input:]


def ham_com(src: List[List[int]], s_num: int, encode=True) -> None:
    s_range = range(s_num)
    global sumaa

    for i in src:
        sindrome = 0
        for s in s_range:
            sind = 0
            for p in range(2 ** s, len(i) + 1, 2 ** (s + 1)):
                for j in range(2 ** s):
                    if (p + j) > len(i):
                        break
                    sind ^= i[p + j - 1]

            if encode:
                i[2 ** s - 1] = sind
            else:
                sindrome += (2 ** s * sind)

        if (not encode) and sindrome:
            i[sindrome - 1] = int(not i[sindrome - 1])


def encoder(msg: str, mode: int=8) -> str:

    result = ""

    msg_b = msg.encode("utf-8")
    s_num = ceil(log2(log2(mode + 1) + mode + 1))
    bit_seq = []
    for byte in msg_b:
        bit_seq += list(map(int, f"{byte:08b}"))

    res_len = ceil((len(msg_b) * 8) / mode)
    bit_seq += [0] * (res_len * mode - len(bit_seq))

    to_hamming = []

    for i in range(res_len):
        code = bit_seq[i * mode:i * mode + mode]
        for j in range(s_num):
            code.insert(2 ** j - 1, 0)
        to_hamming.append(code)

    ham_com(to_hamming, s_num, True)

    for i in to_hamming:
        result += "".join(map(str, i))

    return result


def decoder(msg: str, mode: int=8) -> str:

    result = ""

    s_num = ceil(log2(log2(mode + 1) + mode + 1))
    res_len = len(msg) // (mode + s_num)
    code_len = mode + s_num

    to_hamming = []

    for i in range(res_len):
        code = list(map(int, msg[i * code_len:i * code_len + code_len]))
        to_hamming.append(code)

    ham_com(to_hamming, s_num, False)

    for i in to_hamming:
        for j in range(s_num):
            i.pop(2 ** j - 1 - j)
        result += "".join(map(str, i))

    msg_l = []

    for i in range(len(result) // 8):
        val = "".join(result[i * 8:i * 8 + 8])
        msg_l.append(int(val, 2))
    try:
        result = bytes(msg_l).decode("utf-8")
    except UnicodeDecodeError:
        return result
    return result


def err_add(msg: str, mode: int) -> str:
    seq = list(map(int, msg))
    s_num = ceil(log2(log2(mode + 1) + mode + 1))
    code_len = mode + s_num
    cnt = len(msg) // code_len
    global errors_add
    global mass_errors
    global all_errors
    global cor_del
    cor_del = cnt
    result = ""

    for i in range(cnt):
        to_noize = seq[i * code_len:i * code_len + code_len]
        noize = randrange(code_len)
        rand1 = randrange(10)
        if rand1 < 6:
            to_noize[noize] = int(not to_noize[noize])
            errors_add += 1
            all_errors += 1
        else:
            to_noize[noize] = int(to_noize[noize])
        result += "".join(map(str, to_noize))
        rand2 = randrange(10)
        if rand2 < 3:
            to_noize = seq[i * code_len:i * code_len + code_len]
            noize = randrange(code_len)
            to_noize[noize] = int(not to_noize[noize])
            result += "".join(map(str, to_noize))
            mass_errors += 1
            all_errors += 1

    return result


if __name__ == "__main__":
    # Длина слова
    MODE = 58

    # Открытие файла с текстом
    file = codecs.open('data.txt', encoding='utf-8', mode='r')

    text = ""

    # Чтение файла
    while True:
        line = file.readline()
        if not line:
            break
        text += line

    print(f'Message:\n{text}')
    
    bin_result = text_to_bits(text)

    key_sum = crc_remainder(bin_result, crc32, '0')
    
    # Кодирование сообщения
    enc_text = encoder(text, MODE)
    #print(f'Encoded:\n{enc_text}')

    print(f'Check sum: {key_sum}')

    # Добавление ошибок
    errors_text = err_add(enc_text, MODE)
    #print(f'With errors:\n{errors_text}')

    # Декодирование сообщения
    dec_text = decoder(errors_text, MODE)
    #print(f'Decoded:\n{dec_text}')

    if mass_errors == 0:
        dec_text = dec_text[:-3]
        bin_result = text_to_bits(dec_text)
        key_sum_aft = crc_remainder(bin_result, crc32, '0')
    else:
        key_sum_aft = crc_remainder(dec_text, crc32, '0')

    print(f'Check sum aft: {key_sum_aft}')

    if key_sum == key_sum_aft:
        print(f'Check sums are identical')
    else:
        print(f'Check sums are not identical')

    # Ошибки
    print(f'All errors: {all_errors}')
    print(f'Errors: {errors_add}')
    print(f'Mass errors: {mass_errors}')
    print(f'Correct errors: {errors_add - mass_errors}')
    print(f'Correctly delivered words: {cor_del - mass_errors}')
    print(f'Wrong delivered words: {mass_errors}')

    file.close()
