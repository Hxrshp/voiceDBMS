import os
import re
import requests

def clean_sql(sql):
    sql = sql.strip()
    if sql.startswith("```"):
        lines = sql.splitlines()
        if len(lines) >= 2:
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            sql = "\n".join(lines).strip()
    # Strip any single backticks or leading/trailing comments/whitespace
    sql = sql.strip("`").strip()
    # If the LLM returned "Generated SQL: SELECT ...", strip the prefix
    if sql.lower().startswith("generated sql:"):
        sql = sql[14:].strip()
        
    # Remove single-line SQL comments (starting with --)
    clean_lines = []
    for line in sql.splitlines():
        line_clean = re.sub(r'--.*$', '', line).strip()
        if line_clean:
            clean_lines.append(line_clean)
    sql = " ".join(clean_lines).strip()
    return sql

def fallback_generate_sql(query):
    query = query.lower().strip()
    
    # 0. CREATE TABLE (DDL)
    if 'create' in query and 'table' in query:
        table_name = None
        named_match = re.search(r'\btable\s+named\s+(\w+)\b', query)
        if named_match:
            table_name = named_match.group(1).strip()
        else:
            before_match = re.search(r'\b(\w+)\s+table\b', query)
            if before_match and before_match.group(1).strip() not in ['create', 'a', 'an', 'another', 'new']:
                table_name = before_match.group(1).strip()
            else:
                simple_match = re.search(r'\btable\s+(\w+)\b', query)
                if simple_match:
                    candidate = simple_match.group(1).strip()
                    if candidate != 'named':
                        table_name = candidate
                    
        if table_name:
            columns_part = re.search(r'\b(?:with|having|columns|containing)\s+(.+)$', query)
            if not columns_part:
                # Default schemas if no columns are specified in the prompt
                if table_name in ['orders', 'order']:
                    return 'CREATE TABLE "orders" ("id" INTEGER PRIMARY KEY, "customer_id" INTEGER, "product" TEXT, "price" REAL);'
                else:
                    return f'CREATE TABLE "{table_name}" ("id" INTEGER PRIMARY KEY, "name" TEXT, "city" TEXT);'
            else:
                cols_text = columns_part.group(1).strip()
                cols_list = []
                for col in cols_text.split(','):
                    col = col.strip()
                    if not col:
                        continue
                    if 'primary key' in col:
                        pk_name = re.search(r'\b(\w+)\b', col)
                        pk = pk_name.group(1) if pk_name else 'id'
                        cols_list.append(f'"{pk}" INTEGER PRIMARY KEY')
                    elif 'price' in col or 'amount' in col:
                        col_clean = re.search(r'\b(\w+)\b', col)
                        name = col_clean.group(1) if col_clean else 'price'
                        cols_list.append(f'"{name}" REAL')
                    elif 'id' in col:
                        col_clean = re.search(r'\b(\w+)\b', col)
                        name = col_clean.group(1) if col_clean else 'id'
                        cols_list.append(f'"{name}" INTEGER')
                    else:
                        col_clean = re.search(r'\b(\w+)\b', col)
                        name = col_clean.group(1) if col_clean else col
                        cols_list.append(f'"{name}" TEXT')
                return f'CREATE TABLE "{table_name}" (' + ', '.join(cols_list) + ');'
    
    # 0.5 ALTER TABLE (DDL)
    if 'add column' in query or 'alter table' in query:
        match = re.search(r'\badd\s+column\s+(\w+)\s+(?:to|in|into)\s+(?:table\s+)?(\w+)\b', query)
        if match:
            col_name = match.group(1).strip()
            table_name = match.group(2).strip()
            col_type = 'TEXT'
            if 'id' in col_name:
                col_type = 'INTEGER'
            elif 'price' in col_name or 'amount' in col_name:
                col_type = 'REAL'
            return f'ALTER TABLE "{table_name}" ADD COLUMN "{col_name}" {col_type};'

    # 0.6 DROP TABLE (DDL)
    if 'drop' in query and 'table' in query:
        table_name = None
        simple_match = re.search(r'\btable\s+(\w+)\b', query)
        if simple_match:
            table_name = simple_match.group(1).strip()
        else:
            before_match = re.search(r'\b(\w+)\s+table\b', query)
            if before_match and before_match.group(1).strip() not in ['drop']:
                table_name = before_match.group(1).strip()
        if table_name:
            return f'DROP TABLE "{table_name}";'

    # 1. DELETE
    if any(word in query for word in ['delete', 'remove', 'discard']):
        id_match = re.search(r'\b(?:id|customer|number|no\.?)\s*(?:is|=)?\s*(\d+)', query)
        if id_match:
            id_val = id_match.group(1).strip()
            return f"DELETE FROM customers WHERE id = {id_val};"
            
    # 2. UPDATE
    if any(word in query for word in ['update', 'change', 'modify', 'set', 'rename']):
        name_update_match = re.search(r'\b(?:change|update|modify)\s+(?:the\s+)?(city|name|location)\s+(?:of|for)\s+([\w\s.-]+?)\s+(?:to|as)\s+([\w\s.-]+?)(?:\s|$)', query)
        if name_update_match:
            field = name_update_match.group(1).strip()
            if field == 'location':
                field = 'city'
            target_name = name_update_match.group(2).strip().title()
            new_val = name_update_match.group(3).strip().title()
            return f"UPDATE customers SET {field} = '{new_val}' WHERE name = '{target_name}';"

        field = 'city' if 'city' in query or 'location' in query else 'name'
        value_match = re.search(r'\b(?:to|as)\s+([\w\s.-]+?)(?:\s+(?:where|for|of|customer)\b|$)', query)
        if value_match:
            new_val = value_match.group(1).strip().title()
            id_match = re.search(r'\b(?:id|customer|number|no\.?)\s*(?:is|=)?\s*(\d+)', query)
            if id_match:
                id_val = id_match.group(1).strip()
                return f"UPDATE customers SET {field} = '{new_val}' WHERE id = {id_val};"
            
            name_search_match = re.search(r'\b(?:for|of|customer)\s+([\w\s.-]+)$', query)
            if name_search_match:
                target_name = name_search_match.group(1).strip().title()
                return f"UPDATE customers SET {field} = '{new_val}' WHERE name = '{target_name}';"

    # 2.5 INSERT ORDER (DML fallback)
    if 'order' in query and any(w in query for w in ['add', 'insert', 'create', 'new']):
        cust_match = re.search(r'\b(?:customer|id|for)\s+(\d+)\b', query)
        prod_match = re.search(r'\b(?:of|product|item)\s+(\w+)\b', query)
        price_match = re.search(r'\b(?:price|cost|amount|for)\s+(\d+)\b', query)
        
        cust_id = cust_match.group(1) if cust_match else "1"
        product = prod_match.group(1).title() if prod_match else "Product"
        price_val = price_match.group(1) if price_match else "0.0"
        
        # If the price match accidentally grabbed customer id, fix it
        if price_match and cust_match and price_match.group(1) == cust_match.group(1):
            all_nums = re.findall(r'\b\d+\b', query)
            if len(all_nums) >= 2:
                price_val = all_nums[1]
        return f"INSERT INTO orders (customer_id, product, price) VALUES ({cust_id}, '{product}', {price_val});"

    # 3. INSERT / ADD
    if any(word in query for word in ['add', 'insert', 'create', 'new', 'register', 'person']):
        city_match = re.search(r'\b(city\s+is|with\s+city|located\s+in|lives\s+in|location\s+of|location\s+is|place\s+is|from|in|city|location|place)\s+([\w\s.-]+)$', query)
        name_match = re.search(r'\b(?:customer|person|named|name\s+is)\s+([\w\s.-]+?)\s+(?:and\s+)?(?:city\s+is|with\s+city|located\s+in|lives\s+in|location\s+of|location\s+is|place\s+is|from|in|city|location|place)\b', query)
        if name_match and city_match:
            name = name_match.group(1).strip().title()
            city = city_match.group(2).strip().title()
            if name.lower().startswith("named "):
                name = name[6:].strip()
            for suffix in [" with", " and", " for"]:
                if name.lower().endswith(suffix):
                    name = name[:-len(suffix)].strip()
            if city.lower().startswith("is "):
                city = city[3:].strip()
            return f"INSERT INTO customers (name, city) VALUES ('{name}', '{city}');"

    # 4. SELECT BY CITY OR FILTER
    name_filter = re.search(r'\b(?:orders|product|products)\s+(?:placed\s+)?(?:by|for|of)\s+(\w+)\b', query)
    if name_filter:
        name_val = name_filter.group(1).strip().title()
        if name_val.lower() not in ['making', 'adding', 'creating', 'updating', 'deleting', 'tracking', 'each', 'all', 'any']:
            return f"SELECT c.name, o.product, o.price FROM orders o JOIN customers c ON o.customer_id = c.id WHERE c.name = '{name_val}';"

    target_table = "customers"
    if any(word in query for word in ["order", "product", "price", "cost"]):
        target_table = "orders"
        
    num_match = re.search(r'\b(\d+)\b', query)
    if num_match and any(w in query for w in ["price", "amount", "cost"]):
        val = num_match.group(1).strip()
        op = "="
        if any(word in query for word in ["more", "greater", "above", "at least", ">"]):
            op = ">="
        elif any(word in query for word in ["less", "below", "under", "<"]):
            op = "<="
        return f"SELECT * FROM {target_table} WHERE price {op} {val};"

    city_filter_match = re.search(r'\b(?:in|from|living\s+in|located\s+in|lives\s+in|city\s+(?:is|of))\s+([\w\s.-]+)', query)
    if city_filter_match:
        city = city_filter_match.group(1).replace('?', '').replace('.', '').strip().title()
        if city and city not in ['all', 'customers', 'customer', 'order', 'orders']:
            return f"SELECT * FROM {target_table} WHERE city = '{city}';"

    # 5. SELECT ALL (DEFAULT FALLBACK)
    return f"SELECT * FROM {target_table};"

def generate_sql(user_query):
    # Try reading the schema
    try:
        with open("schema.txt", "r") as f:
            schema = f.read()
    except Exception:
        schema = "Table: customers\nColumns:\nid INTEGER\nname TEXT\ncity TEXT"

    prompt = f"""You convert natural language into SQL.

Database schema:
{schema}

Guidelines:
- Return ONLY the raw SQL query. Do not add explanations or formatting beyond the SQL itself.
- Extract clean values for name and city. For example, if user says "city andhrapradesh", the city value in SQL should be "Andhrapradesh", not "city andhrapradesh". Do not include label words like "city", "name", or "customer" in the SQL data values.
- Ensure proper string escaping.

User request: {user_query}"""

    # 1. Try Gemini API if key is present
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            response = requests.post(url, json=payload, headers=headers, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                sql = data["candidates"][0]["content"]["parts"][0]["text"]
                if sql:
                    return clean_sql(sql)
            else:
                print(f"Gemini API returned error {response.status_code}: {response.text}. Falling back...")
        except Exception as e:
            print(f"Gemini API failed: {e}. Falling back...")

    # 2. Try Local Ollama (llama3)
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            },
            timeout=2.0
        )
        if response.status_code == 200:
            data = response.json()
            sql = data.get("response", "").strip()
            if sql:
                return clean_sql(sql)
    except Exception as e:
        print(f"Local Ollama failed or not running: {e}. Using fallback parser...")

    # 3. Use local rule-based fallback parser
    return fallback_generate_sql(user_query)