import numpy as np
import pytest
from app.utils.buffers import AudioRingBuffer


def test_ring_buffer_basic_write_read():
    buffer = AudioRingBuffer(capacity=10)
    data = np.arange(5, dtype=np.float32)
    buffer.extend(data)

    result = buffer.get_all()
    assert np.array_equal(result, data)
    assert buffer.size == 5


def test_ring_buffer_overflow():
    buffer = AudioRingBuffer(capacity=10)
    # Write 12 elements into a 10-element buffer
    data = np.arange(12, dtype=np.float32)
    buffer.extend(data)

    result = buffer.get_all()
    # Should contain the last 10 elements
    assert len(result) == 10
    assert np.array_equal(result, np.arange(2, 12, dtype=np.float32))
    assert buffer.size == 10


def test_ring_buffer_wrap_around():
    buffer = AudioRingBuffer(capacity=10)
    # Fill 7 elements
    buffer.extend(np.arange(7, dtype=np.float32))
    # Fill 5 more elements (total 12, causes wrap around)
    buffer.extend(np.arange(100, 105, dtype=np.float32))

    result = buffer.get_all()
    # Expected: [2, 3, 4, 5, 6, 100, 101, 102, 103, 104]
    expected = np.concatenate(
        [np.arange(2, 7, dtype=np.float32), np.arange(100, 105, dtype=np.float32)]
    )
    assert np.array_equal(result, expected)


def test_ring_buffer_clear():
    buffer = AudioRingBuffer(capacity=10)
    buffer.extend(np.arange(5, dtype=np.float32))
    buffer.clear()
    assert buffer.size == 0
    assert len(buffer.get_all()) == 0
