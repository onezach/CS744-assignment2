import os
import torch
import json
import copy
import numpy as np
from torchvision import datasets, transforms
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import logging
import random
import model as mdl
import time
import torch.distributed as dist
from torch.utils.data.distributed import DistributedSampler as DS
import argparse
device = "cpu"
torch.set_num_threads(4)

total_batch_size = 256 # total size of batch for all nodes
def train_model(model, train_loader, optimizer, criterion, epoch, world_size, rank):
    """
    model (torch.nn.module): The model created to train
    train_loader (pytorch data loader): Training data loader
    optimizer (optimizer.*): A instance of some sort of optimizer, usually SGD
    criterion (nn.CrossEntropyLoss) : Loss function used to train the network
    epoch (int): Current epoch number
    """
    # remember to exit the train loop at end of the epoch

    print("Epoch", epoch)
    running_loss = 0.0
    start_time = time.time()
    for batch_idx, (data, target) in enumerate(train_loader):
        # Your code goes here!
        data, target = data.to(device), target.to(device)
        
        # zero the parameter gradients
        optimizer.zero_grad()

        # forward + backward + optimize
        outputs = model(data)
        loss = criterion(outputs, target)
        loss.backward()

        # gradient aggregation
        for param in model.parameters():
            if rank == 0:
                
                gather_list = []
                for i in range(world_size):
                    gather_list.append(torch.empty(param.grad.size()))

                # gather gradients from all participating workers
                dist.gather(tensor=param.grad, gather_list=gather_list)
                
                # elementwise mean (reduced along 0-dimension of stacked gradients)
                e_mean = torch.mean(torch.stack(gather_list), dim=0)
                
                # scatter mean vector
                mean_vector = [e_mean] * world_size
                
                dist.scatter(tensor=param.grad, scatter_list=mean_vector)
            else:
                # workers update gradient with received vector and continue training
                dist.gather(param.grad)
                dist.scatter(param.grad)

        optimizer.step()

        # print statistics
        running_loss += loss.item()

        if batch_idx == 0:    # print at the first mini-batch
            end_time = time.time()
            print(f'[, {batch_idx + 1:5d}] loss: {running_loss:.3f} time: {(end_time - start_time) :.3f}')
            start_time = time.time()
            running_loss = 0.0
        elif batch_idx == 39:    # print at the 40th mini-batch
            end_time = time.time()
            print(f'[, {batch_idx + 1:5d}] loss: {running_loss / 39:.3f} time: {(end_time - start_time) / 39 :.3f}')
            start_time = time.time()
            running_loss = 0.0
        elif (batch_idx+1) %40==0:    # print every 40 mini-batch
            end_time = time.time()
            print(f'[, {batch_idx + 1:5d}] loss: {running_loss / 40:.3f} time: {(end_time - start_time) / 40 :.3f}')
            start_time = time.time()
            running_loss = 0.0

    return None

def test_model(model, test_loader, criterion):
    model.eval()
    test_loss = 0
    correct = 0
    with torch.no_grad():
        for batch_idx, (data, target) in enumerate(test_loader):
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += criterion(output, target)
            pred = output.max(1, keepdim=True)[1]
            correct += pred.eq(target.view_as(pred)).sum().item()

    test_loss /= len(test_loader)
    print('Test set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
            test_loss, correct, len(test_loader.dataset),
            100. * correct / len(test_loader.dataset)))
            

def main(master_ip, world_size, rank):

    # using example from writeup
    master_port = '6585'

    # initialize environment variables
    os.environ['MASTER_PORT'] = master_port
    os.environ['MASTER_ADDR'] = master_ip

    # distributed initialization
    dist.init_process_group(backend="gloo", 
                            init_method=f"tcp://{master_ip}:{master_port}", 
                            rank=rank, 
                            world_size=world_size)

    # set seeds
    torch.manual_seed(11)
    np.random.seed(11)

    # batch size per worker
    batch_size = int(total_batch_size/world_size)

    normalize = transforms.Normalize(mean=[x/255.0 for x in [125.3, 123.0, 113.9]],
                                std=[x/255.0 for x in [63.0, 62.1, 66.7]])
    transform_train = transforms.Compose([
            transforms.RandomCrop(32, padding=4),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            normalize,
            ])

    transform_test = transforms.Compose([
            transforms.ToTensor(),
            normalize])
    training_set = datasets.CIFAR10(root="./data", train=True,
                                                download=True, transform=transform_train)
    sampler = DS(training_set, num_replicas=world_size, rank=rank)
    train_loader = torch.utils.data.DataLoader(training_set,
                                                    num_workers=2,
                                                    batch_size=batch_size,
                                                    sampler=sampler,
                                                    shuffle=False,
                                                    pin_memory=True)
    test_set = datasets.CIFAR10(root="./data", train=False,
                                download=True, transform=transform_test)

    test_loader = torch.utils.data.DataLoader(test_set,
                                              num_workers=2,
                                              batch_size=batch_size,
                                              shuffle=False,
                                              pin_memory=True)
    training_criterion = torch.nn.CrossEntropyLoss().to(device)

    model = mdl.VGG11()
    model.to(device)
    optimizer = optim.SGD(model.parameters(), lr=0.1,
                          momentum=0.9, weight_decay=0.0001)
    # running training for one epoch
    for epoch in range(1):
        train_model(model, train_loader, optimizer, training_criterion, epoch, world_size, rank)
        test_model(model, test_loader, training_criterion)

    dist.destroy_process_group()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--master-ip", required=True)
    parser.add_argument("--num-nodes", required=True, type=int)
    parser.add_argument("--rank", required=True, type=int)

    args = parser.parse_args()

    main(master_ip=args.master_ip, world_size=args.num_nodes, rank=args.rank)
