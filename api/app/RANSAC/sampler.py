from math import comb
import numpy as np
import random

class Sampler:
    def __init__(self, points, num_points: int, num_samples: int):
        """
        This object acts as a interable across a number of samples.
        """
        if not isinstance(points, np.ndarray):
            try:
                points = np.array(points)
            except TypeError as e:
                print("Expected to be able to convert points to a " \
                    f"numpy array, instead got: {e}")
        self.points = points
        self.num_points = num_points
        self.num_samples = num_samples
        self.data_size = self.points.shape[0]

        self.num_samples = min(comb(self.data_size, self.num_points), self.num_samples)

        # Ensure unique samples
        sample = set()
        while len(sample) < self.num_samples:
            indexes = tuple(sorted(random.sample(range(self.data_size), self.num_points)))
            sample.add(indexes)
        sample = list(sample)
        self.sampled_set = [list(item) for item in sample]

    def __len__(self):
        return len(self.sampled_set)

    def __getitem__(self, ind):
        return np.array(self.points[self.sampled_set[ind],:])
