import numpy as np
import threading


class AudioRingBuffer:
    """A thread-safe ring buffer for audio samples."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer = np.zeros(capacity, dtype=np.float32)
        self.write_index = 0
        self.size = 0
        self.lock = threading.Lock()

    def extend(self, data: np.ndarray):
        """Add new samples to the buffer."""
        with self.lock:
            n = len(data)
            if n > self.capacity:
                data = data[-self.capacity :]
                n = self.capacity

            end_space = self.capacity - self.write_index
            if n <= end_space:
                self.buffer[self.write_index : self.write_index + n] = data
            else:
                self.buffer[self.write_index :] = data[:end_space]
                self.buffer[: n - end_space] = data[end_space:]

            self.write_index = (self.write_index + n) % self.capacity
            self.size = min(self.capacity, self.size + n)

    def get_all(self) -> np.ndarray:
        """Retrieve all currently stored samples in order."""
        with self.lock:
            if self.size == 0:
                return np.array([], dtype=np.float32)

            if self.size < self.capacity:
                start = (self.write_index - self.size + self.capacity) % self.capacity
                if start < self.write_index:
                    return self.buffer[start : self.write_index].copy()
                else:
                    return np.concatenate([self.buffer[start:], self.buffer[: self.write_index]])
            else:
                # Full buffer
                return np.concatenate(
                    [self.buffer[self.write_index :], self.buffer[: self.write_index]]
                )

    def clear(self):
        """Clear the buffer."""
        with self.lock:
            self.write_index = 0
            self.size = 0
