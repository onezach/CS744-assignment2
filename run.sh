#!/bin/bash

WORKERS_PORT=('60001' '60002' '60003')
HOST_NAME='cs744@c220g2-011110.wisc.cloudlab.us'
PART_IDS=("2a" "2b" "3")

part() {
    local part_id=$1
    local rank=$2
    local worker_port=$3
    ssh -p "$worker_port" "$HOST_NAME" "cd ~/CS744-assignment2/main/part$part_id && ./run-p$part_id.sh $rank" > "./logs/rank$rank" &
    echo "Started part$part_id with rank $rank on $HOST_NAME:$worker_port"
}

part1() {
    echo "Starting part1"
    cd ~/CS744-assignment2/main/part1 && ./run-p1.sh 0 > ./part1.log
}

main() {
    part1
    # part 2a, 2b, 3
    for part_id in "${PART_IDS[@]}"; do
        mkdir -p ~/CS744-assignment2/main/part$part_id/logs
        cd ~/CS744-assignment2/main/part$part_id && ./run-p$part_id.sh 0 > ./logs/rank0 & # Run the master process
        rank=1
        for worker_port in "${WORKERS_PORT[@]}"; do
            part $part_id $rank $worker_port
            ((rank++))
        done
        wait # Wait for all background processes to complete before proceeding to the next part_id
    done
}

cd ~/CS744-assignment2; git pull
parallel-ssh -i -h hostnames -O StrictHostKeyChecking=no "cd ~/CS744-assignment2; git pull"
main