"""Train SmallCNN on the synthetic quadrant dataset and save the best checkpoint.

    python train.py

Produces checkpoints/best_model.pt as a TorchScript module (via torch.jit.script), which
is what ModelForge's upload endpoint requires for standalone .pt uploads — see
backend/app/services/model_service.py for why arbitrary state_dict checkpoints can't be
accepted without the original model class.
"""

import argparse
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from dataset import QuadrantDataset
from model import SmallCNN

CHECKPOINT_DIR = Path(__file__).parent / "checkpoints"


def evaluate(model: nn.Module, loader: DataLoader) -> float:
    model.eval()
    correct, total = 0, 0
    with torch.no_grad():
        for images, labels in loader:
            predictions = model(images).argmax(dim=1)
            correct += (predictions == labels).sum().item()
            total += labels.size(0)
    return correct / total


def train(epochs: int, batch_size: int, lr: float) -> None:
    train_loader = DataLoader(QuadrantDataset(2000, seed=0), batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(QuadrantDataset(400, seed=1), batch_size=batch_size)

    model = SmallCNN()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    best_accuracy = 0.0
    CHECKPOINT_DIR.mkdir(exist_ok=True)

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(images), labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * images.size(0)

        train_loss = running_loss / len(train_loader.dataset)
        val_accuracy = evaluate(model, val_loader)
        print(f"epoch {epoch}/{epochs}  train_loss={train_loss:.4f}  val_accuracy={val_accuracy:.4f}")

        if val_accuracy > best_accuracy:
            best_accuracy = val_accuracy
            scripted = torch.jit.script(model)
            scripted.save(str(CHECKPOINT_DIR / "best_model.pt"))

    print(f"Best validation accuracy: {best_accuracy:.4f}")
    print(f"Saved TorchScript checkpoint to {CHECKPOINT_DIR / 'best_model.pt'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    args = parser.parse_args()
    train(args.epochs, args.batch_size, args.lr)
