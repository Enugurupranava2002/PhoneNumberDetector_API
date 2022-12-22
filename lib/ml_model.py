import torch
import torch.nn as nn
import torch.nn.functional as F
import torch

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 64, 3)
        self.maxPool1 = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(64, 64, 3)
        self.mpool1 = nn.MaxPool2d(2,2)
        self.fc1 = nn.Linear(25*64, 80)
        self.fc1_drop = nn.Dropout(p=0.2)
        self.fc2 = nn.Linear(80,10)

    def forward(self, x):
        x = torch.reshape(x, (-1,1,28,28))
        x = self.maxPool1(F.relu(self.conv1(x)))
        x = self.mpool1(F.relu(self.conv2(x)))
        x = x.view(x.size(0), -1)
        x = self.fc1_drop(self.fc1(x))
        x = self.fc2(x)
        soft = nn.Softmax(dim=1)
        x = soft(x)
        return x
