from psycopg import sql

# Test the psycopg sql string formatting
print(sql.SQL("UPDATE devices SET {} WHERE build=%s").format(sql.SQL(", ").join([sql.SQL("{} = %s").format(sql.Identifier("foo")), sql.SQL("{} = %s").format(sql.Identifier("bar"))])))
