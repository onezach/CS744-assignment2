#!/bin/bash

WORKERS_PORT=('60001' '60002' '60003')
HOST_NAME='cs744@c220g2-011110.wisc.cloudlab.us'
PART_IDS=("2a" "2b" "3")
LOG_DIR="$HOME/CS744-assignment2/logs"  # Define a base directory for logs

part() {
    local part_id=$1
    local rank=$2
    local worker_port=$3
    # Redirect output to a log file within the log directory
    ssh -p "$worker_port" "$HOST_NAME" "cd $HOME/CS744-assignment2/main/part$part_id && ./run-p$part_id.sh $rank" > "$LOG_DIR/part$part_id/rank$rank.log" 2>&1 &
    echo "Started part$part_id with rank $rank on $HOST_NAME:$worker_port"
}

part1() {
    echo "Starting part1"
    cd $HOME/CS744-assignment2/main/part1 && ./run-p1.sh 0 > "$LOG_DIR/part1/log" 2>&1
}

main() {
    part1
    # part 2a, 2b, 3
    for part_id in "${PART_IDS[@]}"; do
        mkdir -p "$LOG_DIR/part$part_id"
        cd $HOME/CS744-assignment2/main/part$part_id && ./run-p$part_id.sh 0 > "$LOG_DIR/part$part_id/rank0.log" 2>&1 & # Run the master process
        rank=1
        for worker_port in "${WORKERS_PORT[@]}"; do
            sleep 2  # Ensure staggered starts to help avoid port conflicts
            part $part_id $rank $worker_port
            ((rank++))
        done
        wait # Wait for all background processes to complete before proceeding to the next part_id
    done
}

# Ensure base log directory exists
mkdir -p "$LOG_DIR"
cd $HOME/CS744-assignment2; git pull
parallel-ssh -i -h hostnames -O StrictHostKeyChecking=no "cd $HOME/CS744-assignment2; git pull"
main
