import time

def log_loss(batch_idx, running_loss, start_time, named_parameters):

    def print_loss(num_batches):
        nonlocal batch_idx
        nonlocal running_loss
        nonlocal start_time
        end_time = time.time()
        print(f'[, {batch_idx + 1:5d}] loss: {running_loss / num_batches:.3f} time: {(end_time - start_time) :.3f}')
        for name, param in named_parameters:
            print(f"{name}: {param.size()}, gradient size: {param.grad.size()}")
        start_time = time.time()
        running_loss = 0.0

    if batch_idx == 0:    # print at the first mini-batch
        print_loss(1)
    elif batch_idx == 39:    # print at the 40th mini-batch
        print_loss(39)
    elif (batch_idx+1) %40==0:    # print every 40 mini-batch
        print_loss(40)
    elif batch_idx == 195: # the last batch is #195
        print_loss(36)