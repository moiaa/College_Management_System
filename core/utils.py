"""Общие утилиты"""
from typing import List


def calculate_gpa(grades: List[float]) -> float:
    if not grades:
        return 0.0
    return round(sum(grades) / len(grades), 2)
