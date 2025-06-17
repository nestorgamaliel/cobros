
#!/usr/bin/env python3
"""
Punto de entrada principal para el Sistema de Gestion de Cobros Crediticios.
Este script proporciona una interfaz de línea de comandos para interactuar con
el sistema.
"""

import os
import sys
import argparse
import datetime
from app import create_app, get_db_service, get_pago_service
from app.utils.logger import setup_logger
import config


# Configurar logger
logger = setup_logger(__name__)


def main():
    """Funcion principal para ejecutar el programa desde 
    la línea de comandos."""
    parser = argparse.ArgumentParser(description='Sistema de Gestion de Cobros\
                                                Crediticios')
    
    # Subparser para los diferentes comandos
    subparsers = parser.add_subparsers(dest='comando', help='Comandos \
                                            disponibles')
    
    # Comando para registrar un pago
    pago_parser = subparsers.add_parser('pago', help='Registrar un nuevo pago')
    pago_parser.add_argument('--credito_id', type=int, required=True, 
                             help='ID del crédito')
    pago_parser.add_argument('--fecha', type=str, 
                             help='Fecha del pago (YYYY-MM-DD)')
    pago_parser.add_argument('--monto', type=float, required=True, 
                             help='Monto del pago')
    
    # Comando para iniciar el servidor web
    server_parser = subparsers.add_parser('servidor', 
                                          help='Iniciar el servidor web')
    server_parser.add_argument('--host', type=str, default=config.APP_HOST, 
                               help='Host del servidor')
    server_parser.add_argument('--port', type=int, default=config.APP_PORT, 
                               help='Puerto del servidor')
    
    # Comando para crear las tablas en la base de datos
    subparsers.add_parser('crear_tablas', 
                          help='Crear las tablas en la base de datos')
    
    # Comando para comprobar la conexion a la base de datos
    subparsers.add_parser('comprobar_conexion', 
                          help='Comprobar la conexion a la base de datos')
    
    args = parser.parse_args()
    
    # Crear la aplicacion
    app = create_app()
    
    # Obtener los servicios
    db_service = get_db_service()
    pago_service = get_pago_service()
    
    # Ejecutar el comando correspondiente
    if args.comando == 'pago':
        ruta_recibo, nombre_recibo, url_publica = pago_service.registrar_pago(
            args.credito_id, 
            args.fecha or datetime.datetime.now().strftime('%Y-%m-%d'), 
            args.monto,
            args.multa
        )
        
        if ruta_recibo:
            print(f"Pago registrado correctamente")
            print(f"Recibo generado: {ruta_recibo}")
        else:
            print(f"Error al registrar el pago: {nombre_recibo}")
            sys.exit(1)
            
    elif args.comando == 'servidor':
        print(f"Iniciando servidor en http://{args.host}:{args.port}")
        app.run(host=args.host, port=args.port)
        
    elif args.comando == 'crear_tablas':
        db_service.crear_tablas()
        print("Tablas creadas correctamente en la base de datos")
    
    elif args.comando == 'comprobar_conexion':
        if db_service.comprobar_conexion():
            print("Conexion a la  de datos establecida correctamente")
        else:
            print("Error al conectar con la base de datos")
            sys.exit(1)
        
    else:
        parser.print_help()
    
    # Cerrar la conexion a la base de datos si no estamos ejecutando el server
    if args.comando != 'servidor':
        db_service.cerrar()


if __name__ == "__main__":
    main()
