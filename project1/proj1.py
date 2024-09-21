import multiprocessing.connection
import os
import io
from time import sleep
from typing import Dict, List, Tuple
import multiprocessing
import sys
from random import shuffle
from termcolor import colored

"""
TODOS:
[x] create child processes that get the user's...
    [x] name
    [x] age
    [x] favorite color
    [x] favorite food
[x] create queue that holds the child processes ("scheduler")
[x] create loop to execute all of the child processes
[x] have child processes send their data to the parent via a link (i.e., a pipe)
[x] have parent print the data it has received from all of the children

Potential Future Feature (Project 2?):
[] add threading to each child process to track its lifetime 
    [] terminate itself if alive for too long (to save resources) (project 2 (?))
"""


def create_children(
    process_names: List[str],
) -> List[Tuple[str, multiprocessing.connection.Connection, multiprocessing.Process]]:
    scheduler: List[
        Tuple[str, multiprocessing.connection.Connection, multiprocessing.Process]
    ] = []  # store child processes
    new_stdin: io.TextIOWrapper = os.fdopen(
        os.dup(sys.stdin.fileno())
    )  # copy of stdin to pass to children

    # create child processes "p" and load (process name, pipe, process) into the scheduler
    for process_name in process_names:
        parent_conn, child_conn = multiprocessing.Pipe()
        p_process: multiprocessing.Process = multiprocessing.Process(
            target=get_data_from_user, args=(new_stdin, process_name, child_conn)
        )
        process_info: Tuple[
            str, multiprocessing.connection.Connection, multiprocessing.Process
        ] = (process_name, parent_conn, p_process)
        scheduler.append(process_info)

    return scheduler


def run_children(
    scheduler: List[
        Tuple[str, multiprocessing.connection.Connection, multiprocessing.Process]
    ],
) -> Dict[str, str]:
    # start child processes
    for _, _, p_process in scheduler:
        p_process.start()

    sleep(0.5)

    user_data_dict: Dict[str, str] = {}  # store data retrieved from child processes

    while len(scheduler) > 0:
        try:
            print(
                colored("***The scheduler has ", "cyan")
                + colored(len(scheduler), "red"),
                end=" ",
            )
            print(colored("processes left to run***", "cyan")) if len(
                scheduler
            ) > 1 else print(colored("process left to run***", "cyan"))

            p_name, conn, p_process = scheduler.pop(
                0
            )  # get next child process in queue
            try:
                conn.send("START")  # send "START" signal to child process
                user_data: str = conn.recv()  # get data from child via pipe
            except Exception as e:
                print(e)
            p_process.join()  # wait for child to finish

            user_data_dict[p_name] = user_data  # store data received from child
            conn.close()  # close pipe

        except Exception as e:
            print(f"Error in 'while loop': {e}")
            break
    return user_data_dict


def get_data_from_user(
    new_stdin: io.TextIOWrapper,
    data: str,
    child_conn: multiprocessing.connection.Connection,
) -> None:
    process_id: int = os.getpid()
    parent_process_id: int = os.getppid()

    print(
        colored("***A Child (PID: ", "cyan")
        + colored(process_id, "red")
        + colored(") is waiting for signal to start from its Parent (PID: ", "cyan")
        + colored(parent_process_id, "red")
        + colored(")...***", "cyan"),
        flush=True,
    )
    start_signal: str = child_conn.recv()  # waits for "start" signal from parent
    print(
        colored("***A Child (PID: ", "cyan")
        + colored(process_id, "red")
        + colored(") received signal '", "cyan")
        + colored(start_signal, "red")
        + colored("' from its Parent (PID: ", "cyan")
        + colored(parent_process_id, "red")
        + colored(")***", "cyan")
    )

    sys.stdin = new_stdin
    user_input: str = input(
        colored(f"What is your {data}? (enter below)\n", "green")
    ).strip()
    print(
        colored("***A Child (PID: ", "cyan")
        + colored(process_id, "red")
        + colored(") is sending ", "cyan")
        + colored(data, "red")
        + colored(" data to its Parent (PID: ", "cyan")
        + colored(parent_process_id, "red")
        + colored(")***", "cyan")
    )
    child_conn.send(user_input)
    print(
        colored("***A Child (PID: ", "cyan")
        + colored(process_id, "red")
        + colored(") is terminating***", "cyan")
    )
    child_conn.close()


def parent_print_data(data_dict: Dict[str, str]) -> None:
    items: List[Tuple[str, str]] = list(data_dict.items())
    shuffle(items)
    for key, val in items:
        print(colored(f"{key}: ", "green") + colored(val, "red"))


def main() -> None:
    parent_process_pid: int = os.getpid()
    print(
        colored("***The Parent Process has a PID of ", "cyan")
        + colored(parent_process_pid, "red")
        + colored("***", "cyan")
    )
    process_names: List[str] = ["name", "age", "favorite color", "favorite food"]
    shuffle(process_names)

    # create child processes
    scheduler: List[
        Tuple[str, multiprocessing.connection.Connection, multiprocessing.Process]
    ] = create_children(process_names)

    # run child processes
    user_data_dict: Dict[str, str] = run_children(scheduler)

    print(
        colored("***The Parent Process (PID: ", "cyan")
        + colored(parent_process_pid, "red")
        + colored(") will now print the data it has received***", "cyan")
    )

    parent_print_data(user_data_dict)

    print(
        colored("***The Parent Process (PID: ", "cyan")
        + colored(parent_process_pid, "red")
        + colored(") will now terminate***", "cyan")
    )


if __name__ == "__main__":
    main()
