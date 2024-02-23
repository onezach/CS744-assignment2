# Note for Submission

## Environment Setup

If conda is not already installed, `bash ./pre-setup.sh` will install it (yes to all prompts). 

If working on the cluster, run `bash ./post-setup.sh` and you're set. For local development, use `conda env create -f environment.yml` to generate an environment equivalent to what is on the cluster.

## Running the Code

If `make` is installed, `make run-all` from the root directory will run all the parts. This requires the public key of the master to be added to each worker's `authorized_keys` file, including the master itself.

To run a specific part, you have 3 options:

- Run `./run.sh $part$` from the root directory on the master. This requires the public key of the master to be added to each worker's `authorized_keys` file, including the master itself.
- `cd` into the code of each part (e.g. `./main/part1/`) and run `./run-px.sh` (e.g. `./run-p1.sh $rank$`). For part 2a, 2b, and 3, you need to do this on all 4 workers.
- `cd` into the code of each part (e.g. `./main/part1/`) and run `python main.py --master-ip $ip_address$ --num-nodes 4 --rank $rank$`. For part 2a, 2b, and 3, you need to do this on all 4 workers.