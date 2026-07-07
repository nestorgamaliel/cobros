# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import Base, Persona, Credito, Pago, Vendedor, CreditoComision
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class BaseDatos:
    """Servicio unificado para interactuar con la base de datos."""
    
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

    # ==========================================================
    # 1. MÉTODOS GENÉRICOS (CRUD BÁSICO)
    # ==========================================================
    
    def _insertar_generico(self, modelo, **kwargs):
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

    # Inserciones
    def insertar_persona(self, **kwargs): return self._insertar_generico(Persona, **kwargs)
    def insertar_vendedor(self, **kwargs): return self._insertar_generico(Vendedor, **kwargs)
    def insertar_credito(self, **kwargs): return self._insertar_generico(Credito, **kwargs)
    def insertar_comision(self, **kwargs): return self._insertar_generico(CreditoComision, **kwargs)

    # Actualizaciones
    def actualizar_persona(self, persona_id, **kwargs):
        return self._actualizar_generico(Persona, 'persona_id', persona_id, **kwargs)
    
    def actualizar_credito(self, credito_id, **kwargs):
        return self._actualizar_generico(Credito, 'credito_id', credito_id, **kwargs)

    # Obtenciones simples
    def obtener_persona(self, id): return self.session.query(Persona).get(id)
    def obtener_credito(self, id): return self.session.query(Credito).get(id)
    def obtener_vendedor(self, id): return self.session.query(Vendedor).get(id)
    def obtener_pago(self, id): return self.session.query(Pago).filter_by(pago_id=id).first()

    # ==========================================================
    # 2. MÉTODOS ESPECIALES (LÓGICA COMPLEJA / SQL)
    # ==========================================================

    def insertar_pago(self, **kwargs):
        """Usa RETURNING para capturar el ID generado por el Trigger de la DB."""
        try:
            sql = text("""
                INSERT INTO pago (credito_id, fecha, monto, multa, intereses, monto_comision)
                VALUES (:credito_id, :fecha, :monto, :multa, :intereses, :monto_comision)
                RETURNING pago_id
            """)
            result = self.session.execute(sql, kwargs)
            nuevo_pago_id = result.fetchone()[0]
            self.session.commit()
            return self.obtener_pago_compuesto(nuevo_pago_id, kwargs.get('credito_id'))
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al insertar pago: {str(e)}")
            raise

    def obtener_pago_compuesto(self, pago_id, credito_id):
        return self.session.query(Pago).filter_by(pago_id=pago_id, credito_id=credito_id).first()

    def actualizar_url_pago(self, pago_id, credito_id, url_publica):
        try:
            self.session.query(Pago).filter(
                Pago.pago_id == pago_id,
                Pago.credito_id == credito_id
            ).update({"url_recibo": url_publica})
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise

    def obtener_datos_credito(self, credito_id):
        sql = text("""
            SELECT a.credito_id,
                   b.nombres || ' ' || b.apellidos AS cliente,
                   a.fecha AS fecha_credito,
                   a.total_credito_proyectado,
                   a.dia_pago,
                   a.cuota,
                   c.ultima_fecha_pago,
                   a.vendedor_id,
                   (a.total_credito_proyectado - COALESCE(c.pagado, 0)) AS saldo
            FROM credito a
            LEFT JOIN persona b ON (a.persona_id = b.persona_id)
            LEFT JOIN (
                SELECT credito_id,
                       SUM(monto) AS pagado,
                       MAX(fecha) AS ultima_fecha_pago
                FROM pago
                GROUP BY credito_id
            ) c ON (a.credito_id = c.credito_id)
            WHERE a.credito_id = :credito_id
        """)
        try:
            result = self.session.execute(sql, {"credito_id": credito_id}).fetchone()
            if not result: return {}
            return {
                'credito_id': result.credito_id,
                'cliente': result.cliente,
                'fecha_credito': result.fecha_credito,
                'total_credito_proyectado': result.total_credito_proyectado,
                'dia_pago': result.dia_pago,
                'cuota': result.cuota,
                'ultima_fecha_pago': result.ultima_fecha_pago,
                'vendedor_id': result.vendedor_id,
                'saldo': result.saldo if result.saldo is not None else result.total_credito_proyectado
            }
        except Exception as e:
            logger.error(f"Error en obtener_datos_credito: {str(e)}")
            raise

    def buscar_personas(self, filtros, limite=10, pagina=1):
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

    def obtener_cobros_dia(self, dias_lista):
        sql = text("""
            SELECT DISTINCT 
            a.nombres || ' ' || a.apellidos AS cliente, 
            a.cuota, 
            a.dia_pago, 
            a.nombre_vendedor AS vendedor, 
            b.observacion 
            FROM saldos_totales a
            LEFT JOIN credito_gestion b ON (a.credito_id = b.credito_id)
            WHERE ((a.dia_pago IN :dias) OR (EXTRACT(DAY FROM b.fecha_promesa) IN :dias))
            AND a.privado = 2
            ORDER BY a.dia_pago DESC
        """)
        try:
            result = self.session.execute(sql, {"dias": dias_lista}).fetchall()
            return [{
                'cliente': r.cliente, 'cuota': r.cuota, 'dia_pago': r.dia_pago,
                'vendedor': r.vendedor, 'observacion': r.observacion or "Sin obs."
            } for r in result]
        except Exception as e:
            logger.error(f"Error en reporte de cobros: {str(e)}")
            return []

    def cerrar(self):
        self.session.close()


    def insertar_registro_finiquito(self, credito_id, url_documento, monto_cancelado, firmante=None):
            """
            Registra la generación de un nuevo finiquito en la tabla credito_finiquito.
            """
            try:
                # Si no se envía firmante, usamos el valor por defecto
                firmante_final = firmante or "EVELYN YANETH GARCIA BAIRES"
                
                sql = text("""
                    INSERT INTO credito_finiquito (credito_id, url_documento, monto_cancelado, fecha_generacion, firmante)
                    VALUES (:credito_id, :url, :monto, :fecha, :firmante)
                """)
                
                self.session.execute(sql, {
                    "credito_id": credito_id,
                    "url": url_documento,
                    "monto": monto_cancelado,
                    "fecha": datetime.datetime.now(),
                    "firmante": firmante_final
                })
                self.session.commit()
                logger.info(f"Registro de finiquito guardado para crédito {credito_id}")
                return True
            except Exception as e:
                self.session.rollback()
                logger.error(f"Error al insertar en credito_finiquito: {str(e)}")
                raise        

    def obtener_resumen_saldos_vista(self, credito_id):
            """
            Obtiene meses_pendientes, nivel_mora y saldo_total desde la vista saldos_totales.
            """
            sql = text("""
                SELECT meses_pendientes, nivel_mora, saldo_total
                FROM public.saldos_totales
                WHERE credito_id = :credito_id
                LIMIT 1
            """)
            try:
                result = self.session.execute(sql, {"credito_id": credito_id}).fetchone()
                if not result:
                    return None
                return {
                    "meses_pendientes": int(result.meses_pendientes) if result.meses_pendientes is not None else 0,
                    "nivel_mora": result.nivel_mora,
                    "saldo_total": float(result.saldo_total) if result.saldo_total is not None else 0.0
                }
            except Exception as e:
                logger.error(f"Error en obtener_resumen_saldos_vista: {str(e)}")
                raise            