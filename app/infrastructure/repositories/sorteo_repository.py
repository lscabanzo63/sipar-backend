from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.domain.Exeptions.exceptions import DomainError

class SorteoRepo:
    def __init__(self, session: Session):
        self.session = session

    def crear_sorteo(self, conjunto_id: int, periodicidad: str) -> int:
        q = text("""
            INSERT INTO public.sorteo (conjunto_residencial_id, periodicidad)
            VALUES (:cid, :per)
            RETURNING id_sorteo
        """)
        try:
            return self.session.execute(q, {"cid": conjunto_id, "per": periodicidad}).scalar_one()
        except IntegrityError as e:
            # Importante: revertir la transacción antes de relanzar
            self.session.rollback()
            # Detecta tu constraint por nombre o por mensaje
            if "uniq_sorteo_conjunto" in str(e.orig) or "conjunto_residencial_id" in str(e.orig):
                raise DomainError(
                    409,
                    "ERR_SORTEO_DUPLICADO_CONJUNTO",
                    "Ya existe un sorteo configurado para este conjunto."
                ) from e
            raise

    def insertar_fechas(self, sorteo_id: int, fechas: list):
        if not fechas: 
            return
        q = text("INSERT INTO public.sorteo_fecha (sorteo_id, fecha) VALUES (:sid, :fecha)")
        self.session.execute(q, [{"sid": sorteo_id, "fecha": f} for f in fechas])

    def mapear_norma_por_nombre(self, nombre_normalizado: str):
        normadb = 'ROTACIÓN' if nombre_normalizado == 'ROTACION' else nombre_normalizado
        q = text("SELECT id_norma FROM public.norma WHERE UPPER(nombre_norma)=UPPER(:n) LIMIT 1")
        return self.session.execute(q, {"n": normadb}).scalar_one_or_none()

    def insertar_normas(self, sorteo_id: int, normas: list[dict]):
        for n in normas:
            if not n.get("activa"):
                continue
            nid = self.mapear_norma_por_nombre(n.get("tipo","").strip().upper())
            if nid is None:
                raise DomainError(400, "ERR_NORMA_DESCONOCIDA", f"No se encontró la norma '{n.get('tipo')}'.")
            parametro = None
            if n.get("tipo") == "ROTACION" and n.get("parametros"):
                parametro = str(n["parametros"].get("n")) if n["parametros"].get("n") is not None else None
            q = text("""
                INSERT INTO public.sorteo_norma (sorteo_id, norma_id, parametro)
                VALUES (:sid, :nid, :parametro)
                ON CONFLICT (sorteo_id, norma_id) DO UPDATE SET parametro = EXCLUDED.parametro
            """)
            self.session.execute(q, {"sid": sorteo_id, "nid": nid, "parametro": parametro})

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
