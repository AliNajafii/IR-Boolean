# About Project
This project Is based on Christopher D. Manning, Hinrich Schütze, and Prabhakar Raghavan's book (Introduction to Information Retrieval).

The goal is to reach a better systems for querieng among bunch of data with high precision.

## Boolean Query Support
In first stage I developed a mechanism to search boolean expressions.
Boolean query expression is discussed [here](https://nlp.stanford.edu/IR-book/pdf/01bool.pdf "here") .
It parses boolean expressions by Parse Tree (Expression Tree) to itrate expressions in Postorder manner. For Example the results of searching `(hello or hi) and not fine` in `./toy-data` directory is `hello.txt,hello2.txt`. 

------------


**Note :**  parentheses are so importatnt to make you available to get the expected results. for example if you type `hello or hi and not fine` in the above example the results would be : `fine3.txt,hello.txt,hello2.txt` which is completely diffrent.

------------

