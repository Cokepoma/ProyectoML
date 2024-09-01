from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.email import EmailOperator
from datetime import datetime, timedelta
from a_get_start_date import get_start_date
from b_get_data import query_mssql
from c_process_data import process_data, branch_task_c
from d_execution_time import execution_time , branch_task_d

# Default arguments for the DAG
default_args = {
    'owner': 'Jorge Pons',
    'depends_on_past': False,
    'email' : ['jorgepons90@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# DAG definition
dag = DAG(
    'Apriori_project',
    default_args=default_args,
    description='Apriori project',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 8, 1),
    catchup=False,
)


# Task a: get the date and time the execution started
start_task = PythonOperator(
    task_id = 'start_task',
    python_callable = get_start_date,
    dag = dag
)


# Task b: Obtain data from the database to start the analysis 
get_data = PythonOperator(
    task_id='get_data',
    python_callable=query_mssql,
    dag=dag
)

# Branching task based on process outcome
branch_task = BranchPythonOperator(
    task_id='branch_task',
    python_callable=branch_task_c,
    provide_context=True,
    )

# Task c: Process data (Perform analysis with apriori algorithm and insert the result into the database)
processing_data = PythonOperator(
    task_id='processing_data',
    python_callable=process_data,
    provide_context=True,
    dag=dag,
)

# Branching task based on process outcome
branch_task_dd = BranchPythonOperator(
    task_id='branch_task_dd',
    python_callable=branch_task_d,
    provide_context=True,
    )

# Task : Send email notification if execution was successful
send_email = EmailOperator(
    task_id='send_email',
    to='algenet4.jpons@gmail.com',
    subject='DAG simple_dag completed',
    html_content='The DAG simple_dag has been successfully executed.',
    dag=dag,
)
# Task : Send email notification if execution was successful
send_failure_email = EmailOperator(
    task_id='send_failure_email',
    to='algenet4.jpons@gmail.com',
    subject='DAG simple_dag failed',
    html_content='The DAG simple_dag failed.',
    dag=dag,
)

# Task d: Calculate the execution time and add the result to the database to obtain an audit table 

calculate_execution_time  = PythonOperator(
    task_id='calculate_execution_time',
    python_callable=execution_time,
    provide_context=True,
    dag=dag,
)


start_task >> get_data >> branch_task
branch_task >> [processing_data,send_failure_email]
processing_data >> branch_task_dd
branch_task_dd >> [send_email,send_failure_email]
send_email >> calculate_execution_time
send_failure_email 


