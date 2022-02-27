# Project 2

## **Task description**

### *Write a program that implements a distributed application for managing queues*

<br/>

## **Idea**
- Restaurant
    - types of threads? processes?
        - customers 
            - place orders (i.e., requests to a server)
            - for simplicity, assume customer "calls the order in" (no need for waiter/waitresses)
        - chefs
            - created (aka "hired") beforehand; sitting in a waiting queue 
            - take an order (from queue) and make food (i.e., handle the request and send back once completed)
            - for simplicity, assume chef puts order in bag as part of "task duration"

<br/>

## **TODOs**
- [ ] create restaurant
    - [x] create menu items
        - [x] name
        - [x] time to prepare
        - [x] price
    - [x] create job queue
    - [x] create cash register (i.e., place to store all money made)
- [ ] create customers
    - [ ] create order (varying timing?)
    - [ ] create time tracker (i.e., moment they place order to when they receive their meal)
- [ ] create chefs
    - [x] take order from queue
    - [x] keep track of how many orders chef has handled
    - [ ] return meal to customer (i.e., send signal via pipe)
    - [ ] put money from meal into cash register