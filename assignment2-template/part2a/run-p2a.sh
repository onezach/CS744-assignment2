# This script will only work with our current setup and is not designed for general use.

# $1: rank (0-3)

if [ $# != 1 ]; then
    echo "Must provide rank (0 to 3)."
    exit 1
fi

python main.py --master-ip '172.18.0.2' --num-nodes 4 --rank $1
