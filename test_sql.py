import psycopg
from psycopg import sql

query = sql.SQL("UPDATE devices SET {} = %s WHERE build=%s").format(sql.Identifier("builds"))
print(query)
