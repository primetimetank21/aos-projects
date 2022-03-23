# Project 2

## **Task description**

### *Write a program that uses (a) POSIX semaphores to provide mutual exclusion and (b) UNIX shared memory segments to store shared variables*

<br/>

## **Idea**
- [x] Processes are all trying to perform an operation on some element in an array (shared between them)
    - [x] 4 processes (add, sub, square, sqrt)
    - [x] only one can access array at a time (use semaphore)
    - [x] check if possible to perform operation on value
    - [x] perform operation and print out current elements in array
    - [x] make **VERY** verbose!!
