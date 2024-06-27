# Report for Assignment 1

## Project chosen

Name: Flask

URL: https://github.com/pallets/flask

Number of lines of code and the tool used to count it: 782430 counted using Lizard

Programming language: Python

## Coverage measurement

### Existing tool

The existing tool used for measuring coverage is coverage.py. It was executed using the following command:

```coverage run -m pytest```

![Coverage results with the Coverage.py tool](./images/Coverage.png)

### Your own coverage tool

Group member name: Jannes van den Bogert

Function 1 name: 'get_send_file_max_age'

Commit made: [get_send_file_max_age](https://github.com/pallets/flask/commit/3c984992b97935e17d8f2d42c84128b397cd0e7e)

![JSON Dumb file for the results](./images/JsonDumpDisGet.png)
![The coverage before writing a test](./images/Old_Get_Send_File_Max.png)


Function 2 name: dispatch_request

Commit made: [Commit for dispatch_request](https://github.com/pallets/flask/commit/3c984992b97935e17d8f2d42c84128b397cd0e7e)

![JSON Dumb file for the results](./images/JsonDumpDisGet.png)
![The coverage before writing a test](./images/Old_Dispatch.png)

## Coverage improvement

### Individual tests

Group member name: Jannes van den Bogert

Test 1 name: test_get_send_file_max_age

Commit made: [Commit for test_make_config.py](https://github.com/pallets/flask/compare/main...wasimic311:flask:dev_test_jannes)

![The coverage before writing a test](./images/Old_Get_Send_File_Max.png)

![The coverage after writing a test](./images/New_Get_Send_File_Max.png)

The coverage improved by 54%, from 46% to 100%.

Test 2 name: test_dispatch_request

Commit made: [Commit for test_make_config.py](https://github.com/pallets/flask/compare/main...wasimic311:flask:dev_test_jannes)

![The coverage before writing a test](./images/Old_Dispatch.png)

![The coverage after writing a test](./images/New_Dispatch.png)

The coverage improved by 58%, from 42% to 100%.

### Overall

![The overall coverage before writing any tests](./images/Coverage.png)

![The overall coverage before writing any tests](./images/New_Total_Coverage.png)

## Statement of individual contributions

Jannes van den Bogert: I was responsible for designing and implementing two tests for the Flask application. The tests targeted two specific functions: get_send_file_max_age and dispatch_request. My contributions were helping in enhancing the test coverage from partial to complete for these functions, achieving a significant increase in overall coverage.
