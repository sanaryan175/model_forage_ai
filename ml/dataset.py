"""A tiny, fully synthetic image classification dataset.

Real training runs (gradient descent, backprop, validation) need real data to be
meaningful, but they don't need a large or externally-downloaded dataset to prove the
pipeline works end-to-end offline. Each class is a 32x32 RGB image with one quadrant lit
up plus Gaussian noise — trivially learnable by a small CNN, which lets `train.py`
actually converge in seconds on a CPU with no internet access required.

Swap this for `torchvision.datasets.CIFAR10` or `MNIST` for a real-world dataset; nothing
else in this pipeline (model, training loop, ONNX export) needs to change.
"""

import torch
from torch.utils.data import Dataset

IMAGE_SIZE = 32
NUM_CHANNELS = 3
CLASS_NAMES = ["top_left", "top_right", "bottom_left", "bottom_right"]
NUM_CLASSES = len(CLASS_NAMES)


class QuadrantDataset(Dataset):
    def __init__(self, num_samples: int, seed: int, noise_std: float = 0.25):
        generator = torch.Generator().manual_seed(seed)
        self.labels = torch.randint(0, NUM_CLASSES, (num_samples,), generator=generator)
        self.images = torch.randn(
            num_samples, NUM_CHANNELS, IMAGE_SIZE, IMAGE_SIZE, generator=generator
        ) * noise_std

        half = IMAGE_SIZE // 2
        quadrant_slices = [
            (slice(0, half), slice(0, half)),
            (slice(0, half), slice(half, IMAGE_SIZE)),
            (slice(half, IMAGE_SIZE), slice(0, half)),
            (slice(half, IMAGE_SIZE), slice(half, IMAGE_SIZE)),
        ]
        for i in range(num_samples):
            row_slice, col_slice = quadrant_slices[self.labels[i].item()]
            self.images[i, :, row_slice, col_slice] += 1.5

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int):
        return self.images[idx], self.labels[idx]
