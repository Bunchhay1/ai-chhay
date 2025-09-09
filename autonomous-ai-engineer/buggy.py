import logging

logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    result = 1 + "a"
    print(f"Result: {result}")
except TypeError as e:
    logging.error(f"Error: {e}, Operand types: {type(1)}, {type('a')}")
