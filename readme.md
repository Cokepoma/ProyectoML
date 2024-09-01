
**Important!** Please review the following instructions:

1. Visit the official Airflow website:
   [Airflow Docker Compose Documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)

2. Download Docker Compose. To do this, open the terminal and run the following command:
   ```bash
   curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.10.0/docker-compose.yaml' 

3. Create the necessary folders:
    ```bash
    mkdir -p ./dags ./logs ./plugins ./config
    echo -e "AIRFLOW_UID=$(id -u)" > .env

4. Create a .env file and add the folowing line:
    AIRFLOW_UID=50000

5. add credentials to your mail to send the final mail 
    AIRFLOW__EMAIL__EMAIL_BACKEND: 'airflow.utils.email.send_email_smtp'
    AIRFLOW__SMTP__SMTP_HOST: 'smtp.gmail.com'
    AIRFLOW__SMTP__START_TLS: 'False'
    AIRFLOW__SMTP__SMTP_SSL: 'False'
    AIRFLOW__SMTP__SMTP_USER: ${SMTP_USER}
    AIRFLOW__SMTP__SMTP_PASSWORD: ${SMTP_PASSWORD}
    AIRFLOW__SMTP__SMTP_PORT: '587'
    AIRFLOW__SMTP__SMTP_MAIL_FROM: ${SMTP_MAIL_FROM}

6. create your dags inside dags folder

7. Configure airflow.cfg to populate mail credentials from [SMTP] 
    1. run worker contaner docker exec -it name_container /bin/bash 
    2. copy airflow.cfg inside config folder
        cp airflow.cfg config/airflow.cfg
    3. fill smtp arguments       
        smtp_host = smtp.gmail.com
        smtp_starttls = True
        smtp_ssl = False
        smtp_user = your_user
        smtp_password = your_password
        smtp_port = 587
        smtp_mail_from = your_mail
        smtp_timeout = 30
        smtp_retry_limit = 5
    4. copy new airflow.cfg inside the container
        cp config/airflow.cfg airflow.cfg 

8. configure database connection in aiflow webserver 
    1. go to airflow webserver http://localhost:8080
    2. admin >> connection >> new
    3. in this example:
        Connection Id : my_mssql_conn_id
        Connection Type : Microsoft SQL Server
        Host  : my_host 
        Schema : empty
        Login : User_database
        Password : User Password
        port : MSSQL -> 1433

9. configure mail connection in airflow webserver 
    1. go to airflow webserver http://localhost:8080
    2. admin >> connection >> new
    3. in this example:
        Connection Id : smtp_default
        Connection Type : SMTP
        Host  : smtp.gmail.com 
        Login : your_mail
        Password : your_Password
        port : 587
        from email: your_mail

10. Create final image:
    docker compose up --build
