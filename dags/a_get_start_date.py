
def get_start_date(**kwargs):
    ti = kwargs['ti']
    start_date = ti.start_date
    get_date = ti.xcom_push(key = 'dag_start_date' , value = start_date)
    return get_date
