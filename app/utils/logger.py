import logging
import os


def setup_logger(name):
    """
    Configura y devuelve un logger con el nombre especificado.
    """
    # Configuracion básica del logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    # Crear un logger específico para el modulo
    logger = logging.getLogger(name)
    
    # Personalizar el nivel de log según una variable de entorno
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    logger.setLevel(getattr(logging, log_level))
    
    return logger