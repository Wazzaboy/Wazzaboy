"""Time-ordered split helpers."""

from __future__ import annotations


def walk_forward_splits(n_rows: int, train_size: int, test_size: int, step: int) -> list[tuple[slice, slice]]:
    if min(n_rows, train_size, test_size, step) <= 0:
        raise ValueError("all sizes must be positive")
    if train_size + test_size > n_rows:
        raise ValueError("train_size + test_size must be <= n_rows")

    splits: list[tuple[slice, slice]] = []
    start = 0
    while True:
        train_start = start
        train_end = train_start + train_size
        test_end = train_end + test_size
        if test_end > n_rows:
            break
        splits.append((slice(train_start, train_end), slice(train_end, test_end)))
        start += step
    return splits
