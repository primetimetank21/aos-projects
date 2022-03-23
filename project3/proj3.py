from multiprocessing import shared_memory, Semaphore, Process
from time import sleep
import numpy as np
import math
from random import randint

def print_current_values(name, arr, idx_changed) -> None:
    print(f"Shared array after {name:<6}: {arr} (modified arr[{idx_changed}])\n")

def add(blk_name, semaphore, shape, iterations) -> None:
    #access intial shared copy
    existing_shm = shared_memory.SharedMemory(name=blk_name, create=False)
    arr = np.ndarray(shape, dtype=np.int64, buffer=existing_shm.buf)
    for _ in range(iterations):
        with semaphore:
            num = randint(1, max(arr))
            idx = randint(0,arr.size-1)
            arr[idx] += num
            print(f"{add.__name__:<6} added {num} to {arr[idx] - num}")
            print_current_values(add.__name__, arr, idx)
        sleep(randint(1,3))
    #clean up
    existing_shm.close()

def sub(blk_name, semaphore, shape, iterations) -> None:
    #access intial shared copy
    existing_shm = shared_memory.SharedMemory(name=blk_name, create=False)
    arr = np.ndarray(shape, dtype=np.int64, buffer=existing_shm.buf)
    for _ in range(iterations):
        with semaphore:
            num = randint(1, max(arr))
            idx = randint(0,arr.size-1)
            arr[idx] -= num
            print(f"{sub.__name__:<6} subtracted {num} from {arr[idx] + num}")
            print_current_values(sub.__name__, arr, idx)
        sleep(randint(1,3))
    #clean up
    existing_shm.close()

def square(blk_name, semaphore, shape, iterations) -> None:
    #access intial shared copy
    existing_shm = shared_memory.SharedMemory(name=blk_name, create=False)
    arr = np.ndarray(shape, dtype=np.int64, buffer=existing_shm.buf)
    for _ in range(iterations):
        with semaphore:
            idx = randint(0,arr.size-1)
            num = arr[idx]
            arr[idx] = num**2
            print(f"{square.__name__:<6} squared {num}")
            print_current_values(square.__name__, arr, idx)
        sleep(randint(1,3))
    #clean up
    existing_shm.close()

def sqrt(blk_name, semaphore, shape, iterations) -> None:
    #access intial shared copy
    existing_shm = shared_memory.SharedMemory(name=blk_name, create=False)
    arr = np.ndarray(shape, dtype=np.int64, buffer=existing_shm.buf)
    for _ in range(iterations):
        with semaphore:
            idx = randint(0,arr.size-1)
            num = arr[idx]
            if num < 0:
                print(f"{sqrt.__name__:<6} couldn't take sqrt of {num} (it is negative)")
                continue
            arr[idx] = math.floor(math.sqrt(num))
            print(f"{sqrt.__name__:<6} took sqrt of {num}")
            print_current_values(sqrt.__name__, arr, idx)
        sleep(randint(1,3))
    #clean up
    existing_shm.close()

def create_processes(params) -> list:
    """
    Create processes that will modify shared memory variables
    """
    return [
        Process(target=add, args=params),
        Process(target=sub, args=params),
        Process(target=square, args=params),
        Process(target=sqrt, args=params)
    ]


def main():
    arr = np.random.randint(25, size=10)
    #ref: https://docs.python.org/3/library/multiprocessing.shared_memory.html
    shm = shared_memory.SharedMemory(create=True, size=arr.nbytes)
    shared_arr = np.ndarray(arr.shape, dtype=arr.dtype, buffer=shm.buf)
    shared_arr[:] = arr[:]  #copy the original data into shared memory
    
    #params
    shm_name = shm.name
    semaphore = Semaphore()
    shape = shared_arr.shape
    iterations = randint(4, shared_arr.size)
    params = (shm_name, semaphore, shape, iterations)

    #create processes
    processes = create_processes(params)

    #run processes
    for process in processes:
        process.start()

    #wait for all processes to end
    for process in processes:
        process.join()
    
    #clean up
    shm.close() 
    shm.unlink() #only call once!


if __name__ == "__main__":
    main()