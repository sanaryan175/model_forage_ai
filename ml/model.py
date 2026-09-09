"""A small CNN classifier — deliberately simple so it trains in seconds on a CPU and
converts cleanly through every downstream format (TFLite, TensorRT, Core ML)."""

import torch.nn as nn

from dataset import IMAGE_SIZE, NUM_CHANNELS, NUM_CLASSES


class SmallCNN(nn.Module):
    def __init__(self, num_classes: int = NUM_CLASSES):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(NUM_CHANNELS, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),  # 32 -> 16
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),  # 16 -> 8
        )
        flattened_size = 32 * (IMAGE_SIZE // 4) * (IMAGE_SIZE // 4)
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(flattened_size, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, num_classes),
        )

    def forward(self, x):
        return self.classifier(self.features(x))
