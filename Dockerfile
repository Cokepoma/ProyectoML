FROM apache/airflow:2.9.3

USER root

# Actualiza e instala paquetes necesarios en un solo paso
RUN apt-get update && \
    apt-get install -y \
    iputils-ping \
    telnet \
    unixodbc-dev \
    python3-dev \
    libpq-dev \
    build-essential \
    curl \
    gnupg && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER airflow

# Instala los proveedores de Airflow necesarios
RUN pip install apache-airflow-providers-microsoft-mssql --no-warn-script-location

# Copia y instala dependencias de Python desde requirements.txt
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

# Opcional: Instala otros paquetes de Python si es necesario
# RUN pip install pyodbc pandas numpy sqlalchemy mlxtend tqdm

