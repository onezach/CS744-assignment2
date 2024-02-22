#!/bin/bash

WORKERS_PORT=('60000' '60001' '60002' '60003')
HOST_NAME='cs744@c220g2-011110.wisc.cloudlab.us'
PART_IDS=("2a" "2b" "3")
LOG_DIR="$HOME/CS744-assignment2/logs"  # Define a base directory for logs
TIME_STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ) UTC"

part() {
    local part_id=$1 # 2a, 2b, 3
    local rank=$2 # 0, 1, 2, 3
    local worker_port=$3 # 60000, 60001, 60002, 60003
    ssh -p "$worker_port" "$HOST_NAME" "cd $HOME/CS744-assignment2/main/part$part_id && ./run-p$part_id.sh $rank" > "$LOG_DIR/part$part_id/rank$rank.log" &
    echo "Started part$part_id with rank $rank on $HOST_NAME:$worker_port"
}

part1() {
    mkdir -p "$LOG_DIR/part1"  # Ensure the directory exists
    echo "Starting part1"
    cd $HOME/CS744-assignment2/main/part1 && ./run-p1.sh 0 > "$LOG_DIR/part1/log" 
}

main() {
    # part_id argument
    if [ -z "$1" ]; then
        echo "Usage: $0 <part_id>"
        exit 1
    elif [ "$1" == "1" ]; then
        part1
        exit 0
    elif [ "$1" == "2a" ] || [ "$1" == "2b" ] || [ "$1" == "3" ]; then
        part_id=("$1")
    else
        echo "Invalid part_id. Valid part_ids are: 1, 2a, 2b, 3"
        exit 1
    fi
    # part 2a, 2b, 3
    mkdir -p "$LOG_DIR/part$part_id" || echo "Failed to create log directory for part$part_id"
    rank=0
    for worker_port in "${WORKERS_PORT[@]}"; do
        sleep 10  # Ensure staggered starts to help avoid port conflicts
        part $part_id $rank $worker_port
        ((rank++))
    done
    echo "Waiting for part$part_id to complete. This could take a while..."
    wait # Wait for all background processes to complete before exiting
}


mkdir -p "$LOG_DIR" || echo "Failed to create base log directory"
parallel-ssh -i -h hostnames -O StrictHostKeyChecking=no "cd $HOME/CS744-assignment2; git pull"
main $1
if [ "$?" -ne 0 ]; then
    git restore .
    echo "Failed to run part $1, restoring git changes."
    exit 1
else
    git add "$LOG_DIR"; git commit -m "Logs from $TIME_STAMP"
    echo "Logs from $TIME_STAMP have been added to the git repo. Please use your own git credentials to do git push."
fi