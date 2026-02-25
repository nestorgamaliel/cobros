# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import Base, Persona, Credito, Pago, Vendedor, CreditoComision
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class BaseDatos:
    """Servicio genérico para interactuar con la base de datos."""
    
    def __init__(self, db_url):
        self.engine = create_engine(db_url, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.session = self.Session()
        logger.info("Servicio de base de datos inicializado")        
        
    def comprobar_conexion(self):
        try:
            self.session.execute(text('SELECT 1'))
            return True
        except Exception as e:
            logger.error(f"Error de conexión: {str(e)}")
            return False

    # --- MÉTODOS GENÉRICOS DE INSERCIÓN ---
    
    def _insertar_generico(self, modelo, **kwargs):
        """Método privado para reutilizar lógica de inserción."""
        try:
            nuevo_objeto = modelo(**kwargs)
            self.session.add(nuevo_objeto)
            self.session.commit()
            self.session.refresh(nuevo_objeto)
            return nuevo_objeto
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al insertar en {modelo.__tablename__}: {str(e)}")
            raise

    def insertar_persona(self, **kwargs):
        return self._insertar_generico(Persona, **kwargs)

    def insertar_vendedor(self, **kwargs):
        return self._insertar_generico(Vendedor, **kwargs)

    def insertar_credito(self, **kwargs):
        return self._insertar_generico(Credito, **kwargs)

    def insertar_pago(self, **kwargs):
        """
        Mantenemos la lógica especial para pagos por el uso de RETURNING 
        y la sincronización con el Trigger de PostgreSQL.
        """
        try:
            sql = text("""
                INSERT INTO pago (credito_id, fecha, monto, multa, intereses)
                VALUES (:credito_id, :fecha, :monto, :multa, :intereses)
                RETURNING pago_id
            """)
            result = self.session.execute(sql, kwargs)
            nuevo_pago_id = result.fetchone()[0]
            self.session.commit()
            return self.obtener_pago_compuesto(nuevo_pago_id, kwargs.get('credito_id'))
        except Exception as e:
            self.session.rollback()
            raise

    # --- MÉTODOS GENÉRICOS DE OBTENCIÓN ---

    def obtener_persona(self, id):
        return self.session.query(Persona).get(id)

    def obtener_credito(self, id):
        return self.session.query(Credito).get(id)

    def obtener_vendedor(self, id):
        return self.session.query(Vendedor).get(id)

    def obtener_pago(self, id):
        return self.session.query(Pago).filter_by(pago_id=id).first()

    def obtener_pago_compuesto(self, pago_id, credito_id):
        return self.session.query(Pago).filter_by(pago_id=pago_id, credito_id=credito_id).first()

    # --- MÉTODOS GENÉRICOS DE ACTUALIZACIÓN ---

    def _actualizar_generico(self, modelo, id_attr, id_val, **kwargs):
        try:
            obj = self.session.query(modelo).filter(getattr(modelo, id_attr) == id_val).first()
            if not obj: return None
            for key, value in kwargs.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            self.session.commit()
            return obj
        except Exception as e:
            self.session.rollback()
            raise

    def actualizar_persona(self, persona_id, **kwargs):
        return self._actualizar_generico(Persona, 'persona_id', persona_id, **kwargs)

    def actualizar_credito(self, credito_id, **kwargs):
        return self._actualizar_generico(Credito, 'credito_id', credito_id, **kwargs)

    # --- QUERIES COMPLEJOS (Se mantienen igual) ---

    def obtener_datos_credito(self, credito_id):
        # ... (Tu query SQL de saldos proyectados se queda igual)
        pass

    def buscar_personas(self, filtros, limite=10, pagina=1):
        # ... (Tu lógica de filtros ilike se queda igual)
        pass

    def cerrar(self):
        self.session.close()


    def buscar_personas(self, filtros, limite=10, pagina=1):
        """
        Busca personas en la base de datos según los filtros (DUI, nombres, apellidos).
        """
        try:
            from sqlalchemy import and_
            query = self.session.query(Persona)
            
            filtros_aplicados = []
            if filtros.get('dui'):
                filtros_aplicados.append(Persona.dui == filtros['dui'])
            if filtros.get('nombres'):
                filtros_aplicados.append(Persona.nombres.ilike(f"%{filtros['nombres']}%"))
            if filtros.get('apellidos'):
                filtros_aplicados.append(Persona.apellidos.ilike(f"%{filtros['apellidos']}%"))
            
            if filtros_aplicados:
                query = query.filter(and_(*filtros_aplicados))
            
            offset = (pagina - 1) * limite
            return query.order_by(Persona.nombres).offset(offset).limit(limite).all()
        except Exception as e:
            logger.error(f"Error en buscar_personas: {str(e)}")
            raise
        

    def contar_personas_filtradas(self, filtros):
        """
        Cuenta el total de personas para la paginación.
        """
        try:
            from sqlalchemy import and_
            query = self.session.query(Persona)
            
            filtros_aplicados = []
            if filtros.get('dui'):
                filtros_aplicados.append(Persona.dui == filtros['dui'])
            if filtros.get('nombres'):
                filtros_aplicados.append(Persona.nombres.ilike(f"%{filtros['nombres']}%"))
            if filtros.get('apellidos'):
                filtros_aplicados.append(Persona.apellidos.ilike(f"%{filtros['apellidos']}%"))
            
            if filtros_aplicados:
                query = query.filter(and_(*filtros_aplicados))
            
            return query.count()
        except Exception as e:
            logger.error(f"Error en contar_personas_filtradas: {str(e)}")
            raise        