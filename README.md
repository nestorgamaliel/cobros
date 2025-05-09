# Sistema de Gestión de Cobros Crediticios

Sistema modular para gestionar pagos de créditos y generar recibos en formato PDF.

## Características

- Registro de clientes
- Registro de pagos de créditos
- Generación automática de recibos en PDF
- API REST para integración con otros sistemas
- Interfaz de línea de comandos (CLI)

## Requisitos previos

- Python 3.7+
- PostgreSQL

## Instalación

1. Clonar el repositorio:
   ```
   git clone https://github.com/tuusuario/sistema-cobros.git
   cd sistema-cobros
   ```

2. Crear un entorno virtual e instalar dependencias:
   ```
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configurar las variables de entorno:
   ```
   cp .env.example .env
   # Editar el archivo .env con tus configuraciones
   ```

## Uso

### Crear las tablas en la base de datos

```
python run.py crear_tablas
```

### Registrar un pago

```
python run.py pago --credito_id 39 --monto 70 --fecha 2025-4-29
```

### Iniciar el servidor web

```
python run.py servidor --host 0.0.0.0 --port 5000
```

## API REST

### Registrar un pago

POST /pago
```json
{
  "credito_id": 39,
  "monto": 70,
  "fecha": "2025-04-29"
}
```

### Descargar un recibo

GET /recibo/{nombre_recibo}