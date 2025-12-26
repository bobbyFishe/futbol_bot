# mix.py
import random
from typing import List, TypeVar

T = TypeVar('T')


def mix_list(list_original: List[T]) -> List[T]:
    """Перемешивает список используя алгоритм Фишера-Йетса"""
    list_copy = list_original.copy()
    list_length = len(list_copy)

    for i in range(list_length):
        index_aleatory = random.randint(0, list_length - 1)
        list_copy[i], list_copy[index_aleatory] = list_copy[index_aleatory], list_copy[i]

    return list_copy