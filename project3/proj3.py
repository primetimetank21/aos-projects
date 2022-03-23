from multiprocessing import shared_memory, Semaphore, Process
from time import sleep
from termcolor import colored
import numpy as np
import math
import os
from random import randint


def print_current_values(name, arr, idx_changed) -> None:
    """
    Print values in the given array (and highlight the value that has been changed)
    """
    print("Shared array after " + colored(f"Process {name}", "blue") + "'s operation:",end="\t[")
    for i in range(len(arr)):
        if i == idx_changed:
            print(colored(f"{f'{str(arr[i]):<5}' if len(str(arr[i])) <= 5 else f'{str(arr[i])[:5]}...'}", "red"), end=" ")
        else:
            print(colored(f"{f'{str(arr[i]):<5}' if len(str(arr[i])) <= 5 else f'{str(arr[i])[:5]}...'}", "cyan"), end=" ")
    print("]\t(modified " +  colored(f"arr[","red") + colored(str(idx_changed), "green") + colored("]", "red") + ")\n")


def print_current_values_parent(pos, arr) -> None:
    """
    Print values in the given array
    """
    print(f"Shared array at {pos}:\t[",end=" ")
    for i in range(len(arr)):
        print(colored(f"{str(arr[i])}", "cyan"), end=" ")
    print("]\n")


def add(blk_name, semaphore, shape, iterations) -> None:
    """
    Process that increments values in the Shared array
    """
    #access intial shared copy
    existing_shm = shared_memory.SharedMemory(name=blk_name, create=False)
    arr = np.ndarray(shape, dtype=np.int64, buffer=existing_shm.buf)
    pid = os.getpid()
    for _ in range(iterations):
        num = randint(1, max(arr))
        idx = randint(0,arr.size-1)

        #critical section
        with semaphore:
            arr[idx] += num
            print(colored(f"Process {pid}", "blue") + " added " + colored(str(num), "yellow") + " to " + colored(str(arr[idx] - num), "red") + " (result: " + colored(str(arr[idx]), "red") + ")")
            print_current_values(pid, arr, idx)
        sleep(randint(1,3))
    
    #clean up
    existing_shm.close()
    exit(0)


def sub(blk_name, semaphore, shape, iterations) -> None:
    """
    Process that decrements values in the Shared array
    """
    #access intial shared copy
    existing_shm = shared_memory.SharedMemory(name=blk_name, create=False)
    arr = np.ndarray(shape, dtype=np.int64, buffer=existing_shm.buf)
    pid = os.getpid()
    for _ in range(iterations):
        num = randint(1, max(arr))
        idx = randint(0,arr.size-1)

        #critical section
        with semaphore:
            arr[idx] -= num
            print(colored(f"Process {pid}", "blue") + " subtracted " +  colored(str(num), "yellow") + " from " + colored(str(arr[idx] + num), "red") + " (result: " + colored(str(arr[idx]), "red") + ")")
            print_current_values(pid, arr, idx)
        sleep(randint(1,3))

    #clean up
    existing_shm.close()
    exit(0)


def square(blk_name, semaphore, shape, iterations) -> None:
    """
    Process that squares values in the Shared array
    """
    #access intial shared copy
    existing_shm = shared_memory.SharedMemory(name=blk_name, create=False)
    arr = np.ndarray(shape, dtype=np.int64, buffer=existing_shm.buf)
    pid = os.getpid()
    for _ in range(iterations):
        idx = randint(0,arr.size-1)

        #critical section
        with semaphore:
            num = arr[idx]
            arr[idx] = num**2
            print(colored(f"Process {pid}", "blue") + " squared " + colored(str(num), "red") + " (result: " + colored(str(arr[idx]), "red") + ")")
            print_current_values(pid, arr, idx)
        sleep(randint(1,3))

    #clean up
    existing_shm.close()
    exit(0)


def sqrt(blk_name, semaphore, shape, iterations) -> None:
    """
    Process that takes the square root of values in the Shared array
    """
    #access intial shared copy
    existing_shm = shared_memory.SharedMemory(name=blk_name, create=False)
    arr = np.ndarray(shape, dtype=np.int64, buffer=existing_shm.buf)
    pid = os.getpid()
    for _ in range(iterations):
        idx = randint(0,arr.size-1)

        #critical section
        with semaphore:
            num = arr[idx]
            if num < 0:
                print(colored(f"Process {pid}", "blue") + " couldn't take sqrt of " + colored(str(num), "red") + colored(" (it is negative)", "yellow"))
                print_current_values(pid, arr, idx)
                continue
            arr[idx] = math.floor(math.sqrt(num))
            print(colored(f"Process {pid}", "blue") + " took sqrt of " + colored(str(num), "red") + " (result: " + colored(str(arr[idx]), "red") + ")")
            print_current_values(pid, arr, idx)
        sleep(randint(1,3))

    #clean up
    existing_shm.close()
    exit(0)


def create_processes(params) -> list:
    """
    Create processes that will modify shared memory variables
    """
    return [
        Process(target=add, args=params),   #increments values
        Process(target=sub, args=params),   #decrements values
        Process(target=square, args=params),#squares values
        Process(target=sqrt, args=params)   #square roots values
    ]


def main():
    arr = np.random.randint(low=1, high=7, size=10)
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

    print_current_values_parent("start",shared_arr)

    #run processes
    for process in processes:
        process.start()

    #wait for all processes to end
    for process in processes:
        process.join()
    
    print_current_values_parent("end", shared_arr)

    #clean up
    shm.close() 
    shm.unlink() #only call once!


if __name__ == "__main__":
    main()
