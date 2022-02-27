import os
#maybe make chefs threads and customers processes?
import multiprocessing
import threading
import sys
import time
from typing import Any
import random
# from termcolor import colored
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
        self.job_queue_key = threading.Lock()
        self.chefs = []
        self.menu = {
            "salad": MenuItem("salad",2,2),
            "burger": MenuItem("burger",4,5),
            "fries": MenuItem("fries",3,3),
            "hotDog": MenuItem("hotDog",4,4),
            "pizza": MenuItem("pizza",10,10)
        }
        self.job_queue = []

    def hire_chef(self, chef) -> None:
        """
        Hire Chef (chef should be a Chef)
        """
        chef.restaurant = self
        chef.register_lock = self.register_key
        self.chefs.append(chef)

    def put_money_in_register(self, amount) -> None:
        self.cash_register += amount

    def get_menu_item(self, item_name) -> MenuItem:
        """
        Used by a Chef to get the menu item to prepare
        """
        return self.menu(item_name)

    def add_order(self, item_name, customer_id, phone_number) -> None:
        """
        Used by a Customer to place their order and add it to the job queue
        """
        order = {
            "customer_id": customer_id,     #PID of Customer process
            "phone_number": phone_number,   #pipe connection to Customer process
            "item_name": item_name          #name of menu item
        }
        with self.job_queue_key:
            self.job_queue.append(order)
            print(f"***Added {customer_id}'s order to the job queue***", flush=True)

    def remove_order(self) -> Any:
        """
        Used by a Chef to remove an order from the job queue
        """
        with self.job_queue_key:
            try:
                order = self.job_queue.pop(0)
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

    def handle_order(self):
        """
        Look at current order, cook it (for as long as it needs), and return to customer (using phone_number)
        """
        customer_id = self.current_order.customer_id    #PID of Customer process
        phone_number =  self.current_order.phone_number #pipe connection to Customer process; remember to close!
        item_name = self.current_order.item_name        #name of menu item

        # MenuItem(name, prep_time, price))
        menu_item = self.restaurant.get_menu_item(item_name)
        
        print(f"***Cooking {customer_id}'s order***",flush=True)
        time.sleep(menu_item.prep_time)
        print(f"***Done cooking {customer_id}'s order. Enjoy your {item_name}!***",flush=True)
        phone_number.send("DONE")
        phone_number.close()

        return menu_item.price

    def put_money_in_register(self, amount):
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
        self.restaurant_phone_number = restaurant_phone_number
        self.customer_phone_number = customer_phone_number
        self.start_time = 0
        self.end_time = 0

    def place_order(self) -> None:
        """
        Place order with a restaurant and start timer
        """
        # add_order(self, item_name, customer_id, phone_number)
        self.restaurant.add_order(self.item_name, self.id, self.customer_phone_number)
        self.start_time = time.time()
    
    def wait_for_order(self) -> None:
        """
        Customer waits for Chef to "call" and say that their order is "DONE"
        """
        self.restaurant_phone_number.recv()
        self.end_time = time.time() - self.start_time
        self.restaurant_phone_number.close()
        self.customer_phone_number.close()
        self._leave_review()

    def _leave_review(self):
        """
        Customer shares how long their order took to complete
        """
        print(f"***{self.id} has received their order (took {self.end_time} seconds)***", flush=True)
    

def chef_thread(chef_name, restaurant):
    """
    Function a chef thread will run
    """
    chef = Chef(chef_name)
    restaurant.hire_chef(chef)

    while 1:
        if chef.current_order:
            price = chef.handle_order()
            chef.put_money_in_register(price)
            chef.orders_handled+=1
        else:
            try:
                chef.get_order()
            finally:
                time.sleep(1)



def customer_process(customer_self):
    """
    Function a customer process will run
    """
    pass

def create_customer_processes(restaurant):
    """
    Create customer processes
    """
    item_name = random.choice(list(restaurant.keys()))
    # customer_phone_number, restaurant_phone_number = multiprocessing.Pipe()
    # Customer(item_name, restaurant, phone_number)
    # customer = multiprocessing.Process(target=get_data_from_user, args=(new_stdin, process_name, child_conn))

    # Customer(item_name, restaurant, phone_number)
    pass


def create_chef_threads(num_chefs=4, restaurant=None):
    """
    Calls chef_thread() method to create chef threads
    """
    # chefs = [Chef() for i  in range(num_chefs)]
    # return chefs
    pass


def main():
    pass

if __name__ == "__main__":
    main()