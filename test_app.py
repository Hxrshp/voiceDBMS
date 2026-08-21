import unittest
import json
import os
import sqlite3
from app import app, reset_db
from sql_generator import fallback_generate_sql, generate_sql

class VoiceDBMSTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        self.client = app.test_client()
        # Initialize test database
        reset_db()

    def test_sql_fallback_generator(self):
        # Test SELECT ALL
        self.assertEqual(
            fallback_generate_sql("Show all customers"), 
            "SELECT * FROM customers;"
        )
        self.assertEqual(
            fallback_generate_sql("customers"), 
            "SELECT * FROM customers;"
        )

        # Test SELECT BY CITY
        self.assertEqual(
            fallback_generate_sql("Find customers in Hyderabad"), 
            "SELECT * FROM customers WHERE city = 'Hyderabad';"
        )
        self.assertEqual(
            fallback_generate_sql("Get customers from Delhi"), 
            "SELECT * FROM customers WHERE city = 'Delhi';"
        )

        # Test INSERT
        self.assertEqual(
            fallback_generate_sql("Add a new customer named John from Mumbai"), 
            "INSERT INTO customers (name, city) VALUES ('John', 'Mumbai');"
        )
        self.assertEqual(
            fallback_generate_sql("insert customer Amit in Delhi"), 
            "INSERT INTO customers (name, city) VALUES ('Amit', 'Delhi');"
        )
        self.assertEqual(
            fallback_generate_sql("Add a customer named Harsha and city Andhrapradesh"), 
            "INSERT INTO customers (name, city) VALUES ('Harsha', 'Andhrapradesh');"
        )

        # Test UPDATE
        self.assertEqual(
            fallback_generate_sql("Update customer name to Jane where id is 1"), 
            "UPDATE customers SET name = 'Jane' WHERE id = 1;"
        )
        self.assertEqual(
            fallback_generate_sql("change the city of harsha to mumbai"), 
            "UPDATE customers SET city = 'Mumbai' WHERE name = 'Harsha';"
        )
        self.assertEqual(
            fallback_generate_sql("change the city of harsha as mumbai"), 
            "UPDATE customers SET city = 'Mumbai' WHERE name = 'Harsha';"
        )

        # Test DELETE
        self.assertEqual(
            fallback_generate_sql("Delete customer where id is 5"), 
            "DELETE FROM customers WHERE id = 5;"
        )

        # Test DDL CREATE TABLE
        self.assertEqual(
            fallback_generate_sql("I want to create another table named order with id as primary key , coustmer_id, price, product"),
            'CREATE TABLE "order" ("id" INTEGER PRIMARY KEY, "coustmer_id" INTEGER, "price" REAL, "product" TEXT);'
        )

    def test_api_reset(self):
        response = self.client.post('/api/reset')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn("Database reset", data['message'])

    def test_api_query_select_all(self):
        response = self.client.post('/api/query', 
                                    json={"query": "Show all customers"})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['type'], 'select')
        self.assertEqual(data['headers'], ['id', 'name', 'city'])
        # Sample DB starts with 3 entries
        self.assertEqual(len(data['rows']), 3)
        self.assertIn("SELECT * FROM customers", data['sql'])

    def test_api_query_filter(self):
        response = self.client.post('/api/query', 
                                    json={"query": "Find customers in Hyderabad"})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['rows']), 2) # Rahul and Sita are in Hyderabad

    def test_api_query_insert_and_select(self):
        # 1. Insert a new customer
        response = self.client.post('/api/query', 
                                    json={"query": "Add a new customer named Harsha from Bangalore"})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['type'], 'mutation')

        # 2. Select all customers to confirm addition
        response_all = self.client.post('/api/query', 
                                        json={"query": "Show all customers"})
        data_all = json.loads(response_all.data)
        self.assertEqual(len(data_all['rows']), 4)
        
        # Verify specific details of the last inserted row
        last_row = data_all['rows'][-1]
        self.assertEqual(last_row[1], 'Harsha')
        self.assertEqual(last_row[2], 'Bangalore')

    def test_api_query_invalid_params(self):
        response = self.client.post('/api/query', json={})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], "Query text is required.")

    def test_database_query_integration(self):
        from database_query import run_query
        
        # Test select
        results, headers = run_query("SELECT * FROM customers;")
        self.assertEqual(headers, ['id', 'name', 'city'])
        self.assertTrue(isinstance(results, list))
        
        # Test mutation
        msg, headers = run_query("INSERT INTO customers (name, city) VALUES ('TestUser', 'TestCity');")
        self.assertEqual(msg, "Query executed successfully.")

if __name__ == '__main__':
    unittest.main()
