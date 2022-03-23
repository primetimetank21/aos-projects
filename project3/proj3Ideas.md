# Project 2

## **Task description**

### *Write a program that uses (a) POSIX semaphores to provide mutual exclusion and (b) UNIX shared memory segments to store shared variables*

<br/>

## **Idea**
- [ ] Processes are all trying to perform an operation on some element in an array (shared between them)
    - [ ] 4 processes (add, sub, square, sqrt)
    - [ ] only one can access array at a time (use semaphore)
    - [ ] check if possible to perform operation on value
    - [ ] perform operation and print out current elements in array
    - [ ] make **VERY** verbose!!
