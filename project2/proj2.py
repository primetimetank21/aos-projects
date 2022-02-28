import os
# import sys
#maybe make chefs threads and customers processes?
import multiprocessing
import threading
import time
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
        self.restaurant_phone_number_for_place_order, self.customer_phone_number_for_place_order = multiprocessing.Pipe()
        self.register_key  = threading.Lock()
        self.job_queue_key = threading.Lock()
        self.hiring_manager = threading.Lock()
        self.phone_line_lock = multiprocessing.Lock()
        self.chefs = []
        self.menu = {
            "salad": MenuItem("salad",2,2),
            "burger": MenuItem("burger",4,5),
            "fries": MenuItem("fries",3,3),
            "hotDog": MenuItem("hotDog",4,4),
            "pizza": MenuItem("pizza",10,10)
        }
        self.job_queue = []

    def print_chef_workload(self) -> None:
        total_jobs = 0
        for chef in self.chefs:
            print(colored(f"Chef #{chef.name:<3}", "cyan") + colored(" handled ", "green") + colored(f"{chef.orders_handled}", "cyan") + colored(" jobs", "green"),flush=True)
            total_jobs += chef.orders_handled
        print(colored("Total jobs handled: ", "green") + colored(f"{total_jobs}", "cyan"),flush=True)

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

    def _add_order(self, msg) -> None:
        if not msg: return
        if len(msg) != 3: return
        item_name, customer_id, customer_phone_number = msg
        order = {
            "customer_id": customer_id,             #PID of Customer process
            "phone_number": customer_phone_number,  #pipe connection to Customer process (for pickup order)
            "item_name": item_name                  #name of menu item
        }

        with self.job_queue_key:
                self.job_queue.append(order)
                print(colored(f"***Added {customer_id}'s order to the job queue", "blue") + colored(f" (jobs left: {len(self.job_queue):<4})", "cyan") + colored("***", "blue"), flush=True)

    def add_order(self) -> None:
        """
        Used by a Customer to place their order and add it to the job queue
        """
        while 1:
            msg = self.restaurant_phone_number_for_place_order.recv()
            order_thread = threading.Thread(target=self._add_order, args=(msg,))
            order_thread.daemon = True
            order_thread.start()
            # item_name, customer_id, customer_phone_number = msg
            # order = {
            #     "customer_id": customer_id,             #PID of Customer process
            #     "phone_number": customer_phone_number,  #pipe connection to Customer process (for pickup order)
            #     "item_name": item_name                  #name of menu item
            # }
            # with self.job_queue_key:
            #     self.job_queue.append(order)
            #     print(colored(f"***Added {customer_id}'s order to the job queue", "green") + colored(f" (jobs left: {len(self.job_queue):<4})", "cyan") + colored(f"***", "green"), flush=True)
                # order["phone_number"].send(f"STARTED{customer_id}")


    def remove_order(self) -> dict or None:
        """
        Used by a Chef to remove an order from the job queue
        """
        with self.job_queue_key:
            try:
                if len(self.job_queue) > 0:
                    order = self.job_queue.pop(0)
                    return order
                return None
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
        print(colored(f"***Chef #{self.name} is done cooking {customer_id}'s order. Enjoy your {item_name}!***", "red"),flush=True)
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

    def __init__(self, item_name, restaurant, restaurant_phone_number, customer_phone_number) -> None:
        self.item_name = item_name
        self.restaurant = restaurant
        self.id = os.getpid()
        self.restaurant_phone_number_for_pickup_order = restaurant_phone_number
        self.customer_phone_number_for_pickup_order = customer_phone_number
        self.start_time = 0
        self.end_time = 0

    def place_order(self) -> None:
        """
        Place order with a restaurant and start timer
        """
        with self.restaurant.phone_line_lock:
            self.restaurant.customer_phone_number_for_place_order.send([self.item_name, self.id, self.restaurant_phone_number_for_pickup_order])
        self.start_time = time.time()
    
    def wait_for_order(self) -> None:
        """
        Customer waits for Chef to "call" and say that their order is "DONE"
        """
        ordered_food = self.customer_phone_number_for_pickup_order.recv()
        self.end_time = time.time() - self.start_time
        self.restaurant_phone_number_for_pickup_order.close()
        self.customer_phone_number_for_pickup_order.close()
        self._leave_review(ordered_food)

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
                print(colored(f"***Chef #{chef.name} has taken an order (", "green") + colored(f"{chef.current_order['item_name']}", "cyan") + colored(" for ", "green") +  colored(f"{chef.current_order['customer_id']}", "cyan") + colored(f" (jobs left: {len(restaurant.job_queue)})", "cyan") + colored(")***","green"),flush=True)
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
                time.sleep(1)


def run_customer_process(item_name, restaurant, restaurant_phone_number, customer_phone_number):
    """
    Function a customer process will run
    """
    customer = Customer(item_name, restaurant, restaurant_phone_number, customer_phone_number)
    time.sleep(random.randint(0,5))
    customer.place_order()
    customer.wait_for_order()
    print(colored("***","red") + colored(f"{customer.id}", "cyan") + colored(" has left the restaurant***","red"),flush=True)
    exit(0)


def create_customer_processes(restaurant, num_customers=30):
    """
    Create customer processes
    """
    customer_processes = []
    menu = list(restaurant.menu.keys())
    for _ in range(num_customers):
        item_name = random.choice(menu)
        customer_phone_number, restaurant_phone_number = multiprocessing.Pipe()
        customer_process = multiprocessing.Process(target=run_customer_process, args=(item_name, restaurant, restaurant_phone_number, customer_phone_number))
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
    restaurant_callin = threading.Thread(target=my_restaurant.add_order)
    restaurant_callin.daemon = True
    restaurant_callin.start()
    print(colored(f"***Restaurant has opened for business!***", "red"),flush=True)    

    chefs = create_chef_threads(4, my_restaurant)
    print(colored(f"***Chefs have started working!***", "red"),flush=True)    

    customers = create_customer_processes(my_restaurant, 15)
    print(colored(f"***Customers can begin ordering!***", "red"),flush=True)    

    for chef in chefs:
        chef.start()

    for customer in customers:
        customer.start()

    for customer in customers:
        customer.join()
    

    print(colored(f"***Restaurant has closed for the day***", "green"),flush=True)
    print(colored("Restaurant made ","green") + colored(f"${my_restaurant.print_money_in_register()}","cyan"),flush=True)
    my_restaurant.print_chef_workload()



if __name__ == "__main__":
    main()