import pymysql
from pymysql.cursors import DictCursor

"""
数据库工具类
"""


class DbUtil:
    """构造函数"""

    def __init__(self, host: str, port: int, user: str, password: str, database: str = None):
        """
        mysql 连接配置
        :param host:
        :param port:
        :param user:
        :param password:
        :param database:
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.__conn = pymysql.connect(host=host, port=port, user=user, password=password, database=database)
        # Create a cursor with DictCursor
        self.__cursor = self.__conn.cursor(cursor=DictCursor)
        print(f'Debugging: connect db: {host=}, {port=}, {user=}, {password=}, {database=}')

    def __del__(self):
        """析构函数"""
        self.__cursor.close()
        self.__conn.close()
        print("Debugging: close db!")

    def get_conn(self):
        """获取连接"""
        return self.__conn

    def get_cursor(self, cursor=None):
        """获取游标"""
        return self.__conn.cursor(cursor)

    def commit(self):
        """提交改动"""
        return self.__conn.commit()

    def get_version(self, args=None):
        """获取 DB 版本"""
        self.__cursor.execute("SELECT VERSION()", args)
        version = self.__cursor.fetchone()
        print(f'Debugging: DB Version : {version=}')
        return version

    def select_db(self, db):
        """选择数据库"""
        self.__conn.select_db(db)
        print(f'Debugging: switch database to {db=}')

    def list_databases(self, args=None):
        """查询所有数据库"""
        self.__cursor.execute("SHOW DATABASES", args)
        dbs = []
        for db in self.__cursor.fetchall():
            dbs.append(db[0])
        return dbs

    def list_tables(self, args=None):
        """查询所有表"""
        self.__cursor.execute("SHOW TABLES", args)
        tables = []
        for table in self.__cursor.fetchall():
            tables.append(table[0])
        return tables

    def execute(self, sql, args=None):
        """获取SQL执行结果"""
        self.__cursor.execute(sql, args)
        return self.__cursor.fetchall()

    def get_table_fields(self, db, table, args=None):
        """获取表字段信息"""
        sql = 'SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE table_schema="'+db+'" AND table_name="'+table+'"'
        self.__cursor.execute(sql, args)
        fields = []
        for field in self.__cursor.fetchall():
            fields.append(field[0])
        return fields

    def table_metadata(self, db, table, args=None):
        """查询表字段的元数据信息"""
        db = "'" + db + "'"
        table = "'" + table + "'"
        sql = """
        SELECT 
            column_name,column_type,ordinal_position,column_comment,column_default 
        FROM 
            information_schema.COLUMNS 
        WHERE 
            table_schema = %s AND table_name = %s;
        """ % (db, table)
        self.__cursor.execute(sql, args)
        return self.__cursor.fetchall()

    def query_one(self, sql):
        """查询单条数据"""
        result = None
        try:
            self.__cursor.execute(sql)
            result = self.__cursor.fetchone()
        except Exception as e:
            print(e)
        return result

    def query_all(self, sql):
        """查询多条数据"""
        list_result = ()
        try:
            self.__cursor.execute(sql)
            list_result = self.__cursor.fetchall()
        except Exception as e:
            print(e)
        return list_result


# db info
host = '127.0.0.1'
port = 3306
user = 'root'
password = 'gyl.2015'
database = 'test1'
table = 'user'


if __name__ == "__main__":
    db = DbUtil(host, port, user, password, database)
    db.get_version()

    dbs = db.list_databases()
    print("database list: ", dbs)

    dbs = db.list_tables()
    print("table list: ", dbs)

    print("test1.", table, "fields: ")
    table_metadata = db.get_table_fields("test1", table)
    for metadata in table_metadata:
        print(metadata)
    print()

    print("test1.", table, "metadata: ")
    table_metadata = db.table_metadata("test1", table)
    for metadata in table_metadata:
        print(metadata)
    print()

    db.select_db("test2")

    dbs = db.list_tables()
    print("table list: ", dbs)

    print("test2.", table, "fields: ")
    table_metadata = db.get_table_fields("test2", table)
    for metadata in table_metadata:
        print(metadata)
    print()

    print("test2.", table, "metadata: ")
    table_metadata = db.table_metadata("test2", table)
    for metadata in table_metadata:
        print(metadata)
    print()

    insert_sql = "INSERT INTO user (name, age) VALUES (%s, %s)"
    val = ("user1", "21")
    db.execute(insert_sql, val)
    db.get_conn().commit()

    val = ("user2", "22")
    db.execute(insert_sql, val)
    db.get_conn().commit()

    del db



