from airflow.hooks.base import BaseHook
import pymssql
import pandas as pd


# Función Python que se conecta a MSSQL y ejecuta una consulta
def query_mssql(**kwargs):
    ti = kwargs['ti']
    ti.xcom_push(key='step',value='Task b get data')
    # Obtén la conexión configurada en Airflow
    conn = BaseHook.get_connection('my_mssql_conn_id')
    
    # Parámetros de conexión obtenidos de Airflow
    host = conn.host  # Host del servidor MSSQL
    database = conn.schema  # Nombre de la base de datos
    username = conn.login  # Nombre de usuario
    password = conn.password  # Contraseña
    
    # Conexión a la base de datos
    conn = pymssql.connect(server=host, user=username, password=password, database=database)
    
    try:
          # Ejecución de la consulta
        query = """use AdventureWorks2022;
                    SELECT 
                       SOD.[SalesOrderID]
                      ,SOD.[OrderQty]
                      ,P.Name [ProductID]
                    FROM [AdventureWorks2022].[Sales].[SalesOrderDetail] SOD
                    join [Production].[Product] P on P.ProductID = SOD.ProductID;"""  # Cambia esta consulta según tus necesidades
        
        df = pd.read_sql(query, conn)
        
        # Convertir valores UUID a cadenas
        if 'rowguid' in df.columns:
            df['rowguid'] = df['rowguid'].astype(str)
        
        print('Datos leidos')
        
        ti.xcom_push(key='query_mssql_status', value='success')
        return df 
    except:
        ti.xcom_push(key='query_mssql_status', value='failure')      
    finally:
        conn.close()  