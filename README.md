## Python mysql 

This is th python samply project to 

use fastapi , use demo print "hello world" json object as test
connect mysql using aiohttp aiomysql pool
suggest .env to connect database detail
crud

setup 

Step 1: Create a Virtual Environment and Install Dependencies
First, set up a virtual environment and install the necessary dependencies:
bash
Copy
python -m venv venv
source venv/bin/activate   # On Windows use `venv\Scripts\activate`
pip install fastapi uvicorn aiomysql aiohttp python-dotenv
Step 2: Create a .env File for Database Configuration
Create a file named .env in your project directory and add your database connection details:

Step 3 :

Install uvicorn : 

https://www.uvicorn.org

then run : 
uvicorn main:app --reload   

Happy coding!


Testing the CRUD Operations
You can test the CRUD operations using curl or any API testing tool like Postman:
Create an Item:
bash
Copy
curl -X POST "http://127.0.0.1:8000/items" -H "Content-Type: application/json" -d '{"name": "Item 1", "description": "Description 1"}'
Read an Item:
bash
Copy
curl "http://127.0.0.1:8000/items/1"
Update an Item:
bash
Copy
curl -X PUT "http://127.0.0.1:8000/items/1" -H "Content-Type: application/json" -d '{"id": 1, "name": "Updated Item", "description": "Updated Description"}'
Delete an Item:
bash
Copy
curl -X DELETE "http://127.0.0.1:8000/items/1"
This setup uses FastAPI for the web framework, aiomysql for asynchronous MySQL connections, and environment variables to manage sensitive database connection details. The CRUD operations are performed using basic SQL queries.

