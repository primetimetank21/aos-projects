import os, signal
import multiprocessing
import threading
import time
import datetime
import random
from termcolor import colored
"""
Task Description:
Write a program that implements a distributed application for managing queues.
"""

class MenuItem:
    """
    Objects that a restaurant serves
    """
    def __init__(self, name, prep_time, price) -> None:
        self.name       = name
        self.prep_time  = prep_time
        self.price      = price


class Restaurant:
    """
    Place where Chefs work and Customers order from
    """
    def __init__(self) -> None:
        self.cash_register = 0
        self.register_key  = threading.Lock()
        self.hiring_manager = threading.Lock()
        self.chefs = []
        self.menu = {
            "salad": MenuItem("salad",1,2),
            "burger": MenuItem("burger",3,5),
            "fries": MenuItem("fries",3,3),
            "hotDog": MenuItem("hotDog",2,4),
            "pizza": MenuItem("pizza",5,10)
        }
        # self.job_queue = None
        self.job_queue = multiprocessing.Queue()


    def print_chef_workload(self, num_customers) -> None:
        total_jobs = 0
        for chef in self.chefs:
            print(colored(f"Chef #{chef.name:<3}", "cyan") + colored(" handled ", "green") + colored(f"{chef.orders_handled}", "cyan") + colored(" jobs", "green"),flush=True)
            total_jobs += chef.orders_handled
        print(colored("Total jobs handled: ", "green") + colored(f"{total_jobs}", "cyan"),flush=True)
        print(colored("Total jobs missed: ", "green") + colored(f"{abs(num_customers - total_jobs)}", "cyan"),flush=True)

    def hire_chef(self, chef) -> None:
        """
        Hire Chef (chef should be a Chef)
        """
        chef.restaurant = self
        chef.register_lock = self.register_key
        with self.hiring_manager:
            self.chefs.append(chef)
        print(colored(f"***Chef #{chef.name} has been hired!***", "green"), flush=True)

    def put_money_in_register(self, amount) -> None:
        self.cash_register += amount

    def print_money_in_register(self) -> str:
        return str(self.cash_register)

    def get_menu_item(self, item_name) -> MenuItem:
        """
        Used by a Chef to get the menu item to prepare
        """
        return self.menu[item_name]

    def remove_order(self) -> dict or None:
        """
        Used by a Chef to remove an order from the job queue
        """
        try:
            order = self.job_queue.get(block=True)
            return order
        except:
            return None
        

class Chef:
    """
    Individuals that take orders, prepare them, and add money to register (at their restaurant)
    """

    def __init__(self,chef_name) -> None:
        self.name = chef_name
        self.orders_handled = 0
        self.restaurant = None
        self.current_order = None
        self.register_lock = None

    def get_order(self) -> None:
        """
        Retrieve order from the restaurant's job queue
        """
        order = self.restaurant.remove_order()
        if order:
            self.current_order = order

    def handle_order(self) -> int:
        """
        Look at current order, cook it (for as long as it needs), and return to customer (using phone_number)
        """
        customer_id = self.current_order["customer_id"]    #PID of Customer process
        phone_number =  self.current_order["phone_number"] #pipe connection to Customer process; remember to close!
        item_name = self.current_order["item_name"]        #name of menu item

        # MenuItem(name, prep_time, price))
        menu_item = self.restaurant.get_menu_item(item_name)
        
        print(colored(f"***Chef #{self.name} is cooking {customer_id}'s order***", "white"),flush=True)
        time.sleep(menu_item.prep_time)
        print(colored(f"***Chef #{self.name} is done cooking {customer_id}'s order***", "red"),flush=True)
        phone_number.send(menu_item.name)
        phone_number.close()

        return menu_item.price

    def put_money_in_register(self, amount) -> None:
        """
        Put money into a restaurant's register
        """
        with self.register_lock:
            self.restaurant.put_money_in_register(amount)



class Customer:
    """
    Individuals that place orders (at a restaurant) 
    """

    def __init__(self, item_name, restaurant) -> None:
        self.item_name = item_name
        self.restaurant = restaurant
        self.id = os.getpid()
        self.restaurant_phone_number_for_pickup_order, self.customer_phone_number_for_pickup_order = multiprocessing.Pipe()
        self.start_time = 0
        self.end_time = 0

    def place_order(self) -> None:
        """
        Place order with a restaurant and start timer
        """
        order = {
            "customer_id": self.id, #PID of Customer process
            "phone_number": self.restaurant_phone_number_for_pickup_order, #pipe connection to Customer process
            "item_name": self.item_name #name of menu item
        }
        self.restaurant.job_queue.put(order, block=True)
        print(colored(f"***Added {self.id}'s order to the job queue***","blue"), flush=True)
        self.start_time = datetime.datetime.now()
    
    def wait_for_order(self) -> None:
        """
        Customer waits for Chef to "call" and say that their order is "DONE"
        """
        if self.customer_phone_number_for_pickup_order.poll(60):
            ordered_food = self.customer_phone_number_for_pickup_order.recv()
            self.end_time = datetime.datetime.now() - self.start_time
            self.end_time = self.end_time.total_seconds()
            self.restaurant_phone_number_for_pickup_order.close()
            self.customer_phone_number_for_pickup_order.close()
            self._leave_review(ordered_food)
        else:
            print(colored(f"***{self.id} lost patience and left***", "yellow"), flush=True)
            os.kill(self.id, signal.SIGKILL)



    def _leave_review(self, ordered_food) -> None:
        """
        Customer shares how long their order took to complete
        """
        print(colored(f"***{self.id} has received their order of {ordered_food} (took {self.end_time} seconds)***", "magenta"), flush=True)
    

def run_chef_thread(chef_name, restaurant) -> None:
    """
    Function a chef thread will run
    """
    chef = Chef(chef_name)
    restaurant.hire_chef(chef)

    while 1:
        if chef.current_order:
            try:
                print(colored(f"***Chef #{chef.name} has taken an order (", "green") + colored(f"{chef.current_order['item_name']}", "cyan") + colored(" for ", "green") +  colored(f"{chef.current_order['customer_id']}", "cyan") + colored(")***","green"),flush=True)
                price = chef.handle_order()
                chef.put_money_in_register(price)
                chef.orders_handled+=1
            except Exception as e:
                print(colored(f"***Chef #{chef.name} failed an order***\nReason: {e}", "yellow"),flush=True)
            finally:
                chef.current_order = None
        else:
            try:
                chef.get_order()
            except:
                print(colored(f"***Chef #{chef.name} couldn't find an order in the queue***", "yellow"),flush=True)
            finally:
                time.sleep(0.5)


def run_customer_process(item_name, queue, restaurant):
    """
    Function a customer process will run
    """
    customer = Customer(item_name, restaurant)
    customer.restaurant.job_queue = queue
    time.sleep(random.randint(0,5))
    customer.place_order()
    customer.wait_for_order()
    print(colored("***","red") + colored(f"{customer.id}", "cyan") + colored(" has left the restaurant***","red"),flush=True)
    exit(0)


def create_customer_processes(restaurant, queue, num_customers=multiprocessing.cpu_count()):
    """
    Create customer processes
    """
    customer_processes = []
    menu = list(restaurant.menu.keys())
    for _ in range(num_customers):
        item_name = random.choice(menu)
        # customer_phone_number, restaurant_phone_number = multiprocessing.Pipe()
        customer_process = multiprocessing.Process(target=run_customer_process, args=(item_name, queue, restaurant))
        customer_processes.append(customer_process)

    return customer_processes    


def create_chef_threads(num_chefs=4, restaurant=None) -> list:
    """
    Calls chef_thread() method to create chef threads
    """
    chef_threads = []
    for i in range(num_chefs):
        chef_thread = threading.Thread(target=run_chef_thread,args=(i,restaurant))
        chef_thread.daemon = True
        chef_threads.append(chef_thread)

    return chef_threads


def main():
    my_restaurant = Restaurant()
    print(colored(f"***Restaurant has opened for business!***", "red"),flush=True)
    
    num_chefs = str(input(colored("Enter number of chefs to hire (max: 10)> ","cyan")))
    if num_chefs.strip().replace('\n','') == '':
        print(colored("Invalid amount -- using default amount (4 chefs)","red"),flush=True)
        num_chefs = 4
    elif int(num_chefs) <= 0:
        print(colored("Invalid amount -- using default amount (4 chefs)","red"),flush=True)
        num_chefs = 4
    elif int(num_chefs) > 10:
        print(colored("Invalid amount -- using max amount (10 chefs)","red"),flush=True)
        num_chefs = 10
    else:
        num_chefs = int(num_chefs)

    chefs = create_chef_threads(num_chefs, my_restaurant)
    print(colored(f"***Chefs have started working!***", "red"),flush=True)    

    num_customers = str(input(colored(f"Enter number of customers (min: {num_chefs})> ","cyan")))
    if num_customers.strip().replace('\n','') == '':
        print(colored("Invalid amount -- using default amount (30 customers)","red"),flush=True)
        num_customers = 30
    elif int(num_customers) <= 0:
        print(colored("Invalid amount -- using default amount (30 customers)","red"),flush=True)
        num_customers = 30
    elif int(num_customers) > 100:
        print(colored("Invalid amount -- using \"max\" amount (100 customers)","red"),flush=True)
        num_customers = 100
    else:
        num_customers = int(num_customers)


    customers = create_customer_processes(my_restaurant, my_restaurant.job_queue, num_customers)
    print(colored(f"***Customers can begin ordering!***", "red"),flush=True)    

    for chef in chefs:
        chef.start()

    for customer in customers:
        customer.start()

    for customer in customers:
        customer.join()
    
    print(colored(f"***Restaurant has closed for the day***", "green"),flush=True)
    print(colored("Restaurant made ","green") + colored(f"${my_restaurant.print_money_in_register()}","cyan"),flush=True)
    my_restaurant.print_chef_workload(num_customers)



if __name__ == "__main__":
    main()