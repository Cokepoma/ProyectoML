from airflow.hooks.base import BaseHook
import pymssql
from airflow.models import TaskInstance
from datetime import datetime


def branch_task_d(**kwargs):
    ti = kwargs['ti']
    process_data_status = ti.xcom_pull(key='process_data_status', task_ids='processing_data')
    if process_data_status == 'success':
        return 'send_email'
    else: 
        return 'send_failure_email'

def execution_time(**kwargs):
    # Obtener información del contexto de ejecución
    ti: TaskInstance = kwargs['ti']
    execution_date = ti.execution_date
    start_date = ti.xcom_pull(key= 'dag_start_date',task_ids = 'start_task')
    end_date = datetime.now()
    
    start_date_naive = start_date.replace(tzinfo=None)

    duration = (end_date - start_date_naive)
    duration = duration.total_seconds()

# Recupera el DataFrame desde XComs
    conn = BaseHook.get_connection('my_mssql_conn_id')
    
    # Parámetros de conexión obtenidos de Airflow
    host = conn.host  # Host del servidor MSSQL
    database = conn.schema  # Nombre de la base de datos
    username = conn.login  # Nombre de usuario
    password = conn.password  # Contraseña
    
    # Conexión a la base de datos
    conn = pymssql.connect(server=host, user=username, password=password, database=database)
    cursor = conn.cursor()
    try: 
        # Insertar los datos en la tabla correspondiente
        insert_query = """
        use [AdventureWorks2022];
        INSERT INTO dags_audit (dag_id, execution_date, start_date, end_date, duration)
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (
            ti.dag_id,
            execution_date,
            start_date_naive,
            end_date,
            duration
        ))
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        
    finally:
        cursor.close()
        conn.close()