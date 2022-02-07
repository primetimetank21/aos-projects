import os
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

def create_children(process_names):
	scheduler = []										#store child processes
	new_stdin = os.fdopen(os.dup(sys.stdin.fileno()))	#copy of stdin to pass to children

	#create child processes "p" and load (process name, pipe, process) into the scheduler
	for process_name in process_names:
		parent_conn, child_conn = multiprocessing.Pipe()
		p                       = multiprocessing.Process(target=get_data_from_user, args=(new_stdin, process_name, child_conn))
		process_info            = (process_name, parent_conn, p)
		scheduler.append(process_info)
	
	return scheduler


def run_children(scheduler):
	#start child processes
	for _, _, p_process in scheduler:
		p_process.start()

	user_data_dict = {}	#store data retrieved from child processes

	while len(scheduler) > 0:
		try:
			print(colored("***The scheduler has ", "cyan") + colored(len(scheduler), 'red'), end=" ")
			print(colored("processes left to run***", "cyan")) if len(scheduler) > 1 else print(colored("process left to run***", "cyan"))
			
			p_name, conn, p_process = scheduler.pop(0)	#get next child process in queue
			try:
				conn.send("START")						#send "START" signal to child process
				user_data = conn.recv()					#get data from child via pipe
			except Exception as e:
				print(e)
			p_process.join()							#wait for child to finish

			user_data_dict[p_name] = user_data			#store data received from child
			conn.close()								#close pipe

		except Exception as e:
			print(f"Error in 'while loop': {e}")
			break
	return user_data_dict


def get_data_from_user(new_stdin, data, child_conn):
	print(colored(f"***A Child (PID: ", "cyan") + colored(os.getpid(), "red") + colored(") is waiting for signal to start from its Parent (PID: ","cyan") + colored(os.getppid(), "red") + colored(")...***", "cyan"))
	start_signal = child_conn.recv() #waits for "start" signal from parent
	print(colored(f"***A Child (PID: ", "cyan") + colored(os.getpid(), "red") + colored(") received signal '","cyan") + colored(start_signal, "red") + colored("' from its Parent (PID: ", "cyan") + colored(os.getppid(), "red") + colored(")***", "cyan"))

	sys.stdin  = new_stdin
	user_input = input(colored(f"What is your {data}? (enter below)\n", "green")).strip()
	print(colored(f"***A Child (PID: ", "cyan") + colored(os.getpid(), "red") + colored(") is sending ","cyan") + colored(data, "red") + colored(" data to its Parent (PID: ", "cyan") + colored(os.getppid(), "red") + colored(")***", "cyan"))
	child_conn.send(user_input)
	print(colored(f"***A Child (PID: ", "cyan") + colored(os.getpid(), "red") + colored(") is terminating***","cyan"))
	child_conn.close()


def parent_print(data_dict):
	items = list(data_dict.items())
	shuffle(items)
	for key, val in items:
		print(colored(f"{key}: ", "green") + colored(val,"red"))


def main():
	parent_pid = os.getpid()
	print(colored("***The Parent Process has a PID of ", "cyan") + colored(parent_pid, 'red') + colored("***", "cyan"))
	process_names = ["name", "age", "favorite color", "favorite food"]
	shuffle(process_names)

	#create child processes
	scheduler = create_children(process_names)

	#run child processes
	user_data_dict = run_children(scheduler)
	
	print(colored("***The Parent Process (PID: ", "cyan") + colored(parent_pid, 'red') + colored(") will now print the data it has received***", "cyan"))
	parent_print(user_data_dict)
	print(colored("***The Parent Process (PID: ", "cyan") + colored(parent_pid, 'red') + colored(") will now terminate***", "cyan"))


if __name__ == "__main__":
	main()
