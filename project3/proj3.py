from multiprocessing import shared_memory, Semaphore, Process
from time import sleep
from termcolor import colored
import numpy as np
import math
import os
from random import randint

def print_current_values(name, arr, idx_changed) -> None:
    print(f"Shared array after Process {name}'s operation:",end="\t[ ")#\t{arr} (modified arr[{idx_changed}])\n")
    # for element in arr:
    for i in range(len(arr)):
        if i == idx_changed:
            print(colored(f"{f'{str(arr[i]):<5}' if len(str(arr[i])) < 5 else f'{str(arr[i])[:5]}...'}", "red"), end=" ")
        else:
            print(f"{f'{str(arr[i]):<5}' if len(str(arr[i])) < 5 else f'{str(arr[i])[:5]}...'}", end=" ")
    print(f"]\t(modified arr[{idx_changed}])\n")

def add(blk_name, semaphore, shape, iterations) -> None:
    #access intial shared copy
    existing_shm = shared_memory.SharedMemory(name=blk_name, create=False)
    arr = np.ndarray(shape, dtype=np.int64, buffer=existing_shm.buf)
    pid = os.getpid()
    for _ in range(iterations):
        num = randint(1, max(arr))
        idx = randint(0,arr.size-1)
        with semaphore:
            arr[idx] += num
            print(f"Process {pid} added {num} to {arr[idx] - num} (result: {arr[idx]})")
            print_current_values(pid, arr, idx)
        sleep(randint(1,3))
    #clean up
    existing_shm.close()

def sub(blk_name, semaphore, shape, iterations) -> None:
    #access intial shared copy
    existing_shm = shared_memory.SharedMemory(name=blk_name, create=False)
    arr = np.ndarray(shape, dtype=np.int64, buffer=existing_shm.buf)
    pid = os.getpid()
    for _ in range(iterations):
        num = randint(1, max(arr))
        idx = randint(0,arr.size-1)
        with semaphore:
            arr[idx] -= num
            print(f"Process {pid} subtracted {num} from {arr[idx] + num} (result: {arr[idx]})")
            print_current_values(pid, arr, idx)
        sleep(randint(1,3))
    #clean up
    existing_shm.close()

def square(blk_name, semaphore, shape, iterations) -> None:
    #access intial shared copy
    existing_shm = shared_memory.SharedMemory(name=blk_name, create=False)
    arr = np.ndarray(shape, dtype=np.int64, buffer=existing_shm.buf)
    pid = os.getpid()
    for _ in range(iterations):
        idx = randint(0,arr.size-1)
        with semaphore:
            num = arr[idx]
            arr[idx] = num**2
            print(f"Process {pid} squared {num} (result: {arr[idx]})")
            print_current_values(pid, arr, idx)
        sleep(randint(1,3))
    #clean up
    existing_shm.close()

def sqrt(blk_name, semaphore, shape, iterations) -> None:
    #access intial shared copy
    existing_shm = shared_memory.SharedMemory(name=blk_name, create=False)
    arr = np.ndarray(shape, dtype=np.int64, buffer=existing_shm.buf)
    pid = os.getpid()
    for _ in range(iterations):
        idx = randint(0,arr.size-1)
        with semaphore:
            num = arr[idx]
            if num < 0:
                print(f"Process {pid} couldn't take sqrt of {num} (it is negative)")
                print_current_values(pid, arr, idx)
                continue
            arr[idx] = math.floor(math.sqrt(num))
            print(f"Process {pid} took sqrt of {num} (result: {arr[idx]})")
            print_current_values(pid, arr, idx)
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
    arr = np.random.randint(low=1, high=7, size=10)
    #ref: https://docs.python.org/3/library/multiprocessing.shared_memory.html
    shm = shared_memory.SharedMemory(create=True, size=arr.nbytes)
    shared_arr = np.ndarray(arr.shape, dtype=arr.dtype, buffer=shm.buf)
    shared_arr[:] = arr[:]  #copy the original data into shared memory
    
    #params
    shm_name = shm.name
    semaphore = Semaphore()
    shape = shared_arr.shape
    iterations = randint(3, 7)
    params = (shm_name, semaphore, shape, iterations)

    #create processes
    processes = create_processes(params)

    print(f"Shared array initially: {shared_arr}\n")

    #run processes
    for process in processes:
        process.start()

    #wait for all processes to end
    for process in processes:
        process.join()
    
    print(f"Shared array at end: {shared_arr}\n")

    #clean up
    shm.close() 
    shm.unlink() #only call once!


if __name__ == "__main__":
    main()