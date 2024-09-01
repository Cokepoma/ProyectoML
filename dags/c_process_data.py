from airflow.hooks.base import BaseHook
from mlxtend.frequent_patterns import apriori, association_rules
import pymssql
import pandas as pd
import numpy as np
from tqdm import tqdm

def branch_task_c(**kwargs):
    ti = kwargs['ti']
    query_mssql_status = ti.xcom_pull(key='query_mssql_status', task_ids='get_data')
    if query_mssql_status == 'success':
        return 'processing_data'
    else: 
        return 'send_failure_email'


# Tarea para procesar datos
def process_data(ti, **kwargs):
    try:
        # Recupera el DataFrame desde XComs
        conn = BaseHook.get_connection('my_mssql_conn_id')
        
        # Parámetros de conexión obtenidos de Airflow
        host = conn.host  # Host del servidor MSSQL
        database = conn.schema  # Nombre de la base de datos
        username = conn.login  # Nombre de usuario
        password = conn.password  # Contraseña
        
        # Conexión a la base de datos
        conn = pymssql.connect(server=host, user=username, password=password, database=database)
        df = ti.xcom_pull(task_ids='get_data')
        product_counts = df['ProductID'].value_counts()
        filtered_products = product_counts[product_counts > 10].index  # Solo productos con más de 10 ventas
        df_filtered = df[df['ProductID'].isin(filtered_products)]
        # Preparar la canasta de productos
        basket = df_filtered.groupby(['SalesOrderID', 'ProductID'])['OrderQty'].sum().unstack().reset_index().fillna(0).set_index('SalesOrderID')
        # Función para codificar las celdas
        def hot_encode(x): 
            return 0 if x <= 0 else 1
        # Codificar la canasta
        basket = basket.map(hot_encode)
        # Convertir la canasta a tipo de datos booleano
        basket = basket.astype(bool)
        # Construir el modelo apriori con menor soporte mínimo
        frq_items = apriori(basket, min_support = 0.01, use_colnames = True)
        # Recoger las reglas inferidas en un dataframe con menor umbral de elevación
        rules = association_rules(frq_items, metric ="lift", min_threshold = 0.5)
        rules = rules.sort_values(['confidence', 'lift'], ascending =[False, False])
        # Filtrar reglas donde el consecuente tiene un solo producto
        single_consequents_rules = rules[rules['consequents'].apply(lambda x: len(x) == 1)]

        # Función para obtener la mejor recomendación de upselling
        def recommend_product(current_products, rules):
            applicable_rules = rules[rules['antecedents'].apply(lambda x: set(current_products).issubset(x))]
            if applicable_rules.empty:
                return None
            best_rule = applicable_rules.sort_values(['confidence', 'lift'], ascending=[False, False]).iloc[0]
            recommended_product = list(best_rule['consequents'])[0]
            confidence = best_rule['confidence']
            return recommended_product, confidence


        conn = pymssql.connect(server=host, user=username, password=password, database=database)
        cursor = conn.cursor()
        try:
            # Crear la tabla si no existe
            create_table_query = f"""
            use [AdventureWorks2022];
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Ventas_agrupadas')
            begin
            CREATE TABLE Ventas_agrupadas (
                {', '.join([f"{col} NVARCHAR(MAX)" for col in df.columns])}
            )
            end
            else
            truncate table Ventas_agrupadas
            """
            cursor.execute(create_table_query)
            # Insertar los datos del DataFrame en la tabla
            for index, row in tqdm(df.iterrows(), total=df.shape[0], desc="Procesando filas"):
                insert_query = f"INSERT INTO Ventas_agrupadas ({', '.join(df.columns)}) VALUES ({', '.join(['%s'] * len(row))})"
                cursor.execute(insert_query, tuple(row))
            # Confirmar los cambios
            conn.commit()
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
            
        finally:
            cursor.close()
            conn.close()
        # Convert the sets to strings and calculate their lengths
        rules['antecedents'] = rules['antecedents'].apply(lambda x: ', '.join(sorted(x)))
        rules['consequents'] = rules['consequents'].apply(lambda x: ', '.join(sorted(x)))
        rules['len_antecedents'] = rules['antecedents'].apply(lambda x: len(x.split(', ')))
        rules['len_consequents'] = rules['consequents'].apply(lambda x: len(x.split(', ')))
        # Check the columns of the DataFrame after conversion
        print("Columns in DataFrame after conversion:", rules.columns)

        # Validate that all numeric columns are in the correct format
        numeric_cols = ['antecedent support', 'consequent support', 'support', 'confidence', 'lift', 'leverage', 'conviction', 'zhangs_metric']
        for col in numeric_cols:
            rules[col] = pd.to_numeric(rules[col], errors='coerce')
        # Replace inf values with a large number (or np.nan if you prefer)
        rules.replace([np.inf, -np.inf], np.nan, inplace=True)

        # Round float values to a reasonable precision
        rules[numeric_cols] = rules[numeric_cols].round(5)
        # Drop rows with any NaN values
        rules = rules.dropna()
            
        # Ensure the correct data types
    # Ensure the correct data types after dropping NaNs
        rules = rules.astype({
            'antecedent support': 'float64',
            'consequent support': 'float64',
            'support': 'float64',
            'confidence': 'float64',
            'lift': 'float64',
            'leverage': 'float64',
            'conviction': 'float64',
            'zhangs_metric': 'float64',
            'len_antecedents': 'int64',
            'len_consequents': 'int64'
        })
        conn = pymssql.connect(server=host, user=username, password=password, database=database)
        cursor = conn.cursor()
        try:
            # Create the table 'resultado'
            create_table_query = '''
            use [AdventureWorks2022];
        
            drop table if exists resultado_apriori;
            CREATE TABLE [AdventureWorks2022].dbo.resultado_apriori(
                antecedents nvarchar(max),
                consequents nvarchar(max),    
                [antecedent support] FLOAT,
                [consequent support] FLOAT,    
                [support] FLOAT,
                confidence float,
                lift float,
                leverage float,
                conviction float,
                zhangs_metric float,
                len_antecedents int,
                len_consequents int,
                update_date DATETIME DEFAULT GETDATE()
            )
            '''
            cursor.execute(create_table_query)
            # Insertar los datos del DataFrame en la tabla
        # Bucle para iterar sobre el DataFrame y mostrar la barra de progreso

            for index, row in rules.iterrows():
                insert_query = f"""
                use AdventureWorks2022;
                INSERT INTO [dbo].[resultado_apriori]  
                ({', '.join([f'[{col}]' for col in rules.columns])},[update_date]) VALUES ({', '.join(['%s'] * len(row))},getdate())
                """
                cursor.execute(insert_query, tuple(row))
        
                
            # Confirmar los cambios
            conn.commit()
            
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
            
        finally:
            cursor.close()
            conn.close()
        ti.xcom_push(key='process_data_status', value='success')
    except:
        ti.xcom_push(key='process_data_status', value='failure')
