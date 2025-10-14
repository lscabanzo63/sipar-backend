from typing import Optional, List, Dict
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.domain.Exeptions.exceptions import DomainError

class SorteoRepo:
    def __init__(self, session: Session):
        self.session = session

    # ----- Lectura/lock -----
    def obtener_sorteo_por_conjunto_for_update(self, conjunto_id: int) -> Optional[dict]:
        q = text("""
            SELECT id_sorteo, conjunto_residencial_id, periodicidad, sequence_id
            FROM public.sorteo
            WHERE conjunto_residencial_id = :cid
            FOR UPDATE
        """)
        row = self.session.execute(q, {"cid": conjunto_id}).mappings().first()
        return dict(row) if row else None

    # ----- Crear -----
    def crear_sorteo(self, conjunto_id: int, periodicidad: str) -> dict:
        q = text("""
            INSERT INTO public.sorteo (conjunto_residencial_id, periodicidad)
            VALUES (:cid, :per)
            RETURNING id_sorteo, sequence_id
        """)
        try:
            row = self.session.execute(q, {"cid": conjunto_id, "per": periodicidad}).mappings().one()
            return {"id_sorteo": row["id_sorteo"], "sequence_id": row["sequence_id"]}
        except IntegrityError as e:
            # debería ser raro porque hacemos FOR UPDATE antes, pero por seguridad
            self.session.rollback()
            raise DomainError(409, "ERR_SORTEO_DUPLICADO_CONJUNTO",
                              "Ya existe un sorteo configurado para este conjunto.") from e

    # ----- Actualizar + incrementar sequence -----
    def actualizar_incrementando_sequence(self, sorteo_id: int, periodicidad: str) -> int:
        q = text("""
            UPDATE public.sorteo
            SET periodicidad = :per,
                sequence_id   = sequence_id + 1
            WHERE id_sorteo = :sid
            RETURNING sequence_id
        """)
        new_seq = self.session.execute(q, {"per": periodicidad, "sid": sorteo_id}).scalar_one()
        return int(new_seq)

    # ----- Fechas / Normas -----
    def borrar_fechas(self, sorteo_id: int):
        self.session.execute(text("DELETE FROM public.sorteo_fecha WHERE sorteo_id = :sid"), {"sid": sorteo_id})

    def insertar_fechas(self, sorteo_id: int, fechas: List):
        if not fechas: return
        q = text("INSERT INTO public.sorteo_fecha (sorteo_id, fecha) VALUES (:sid, :fecha)")
        self.session.execute(q, [{"sid": sorteo_id, "fecha": f} for f in fechas])

    def borrar_normas(self, sorteo_id: int):
        self.session.execute(text("DELETE FROM public.sorteo_norma WHERE sorteo_id = :sid"), {"sid": sorteo_id})

    def mapear_norma_por_nombre(self, nombre_normalizado: str) -> Optional[int]:
        normadb = 'ROTACIÓN' if nombre_normalizado == 'ROTACION' else nombre_normalizado
        q = text("SELECT id_norma FROM public.norma WHERE UPPER(nombre_norma)=UPPER(:n) LIMIT 1")
        return self.session.execute(q, {"n": normadb}).scalar_one_or_none()

    def insertar_normas(self, sorteo_id: int, normas: List[Dict]):
        for n in normas:
            if not n.get("activa"): 
                continue
            nid = self.mapear_norma_por_nombre(n.get("tipo","").strip().upper())
            if nid is None:
                raise DomainError(400, "ERR_NORMA_DESCONOCIDA", f"No se encontró la norma '{n.get('tipo')}'.")
            parametro = None
            if n.get("tipo") == "ROTACION" and n.get("parametros"):
                parametro = str(n["parametros"].get("n")) if n["parametros"].get("n") is not None else None
            self.session.execute(text("""
                INSERT INTO public.sorteo_norma (sorteo_id, norma_id, parametro)
                VALUES (:sid, :nid, :parametro)
            """), {"sid": sorteo_id, "nid": nid, "parametro": parametro})

    def commit(self): self.session.commit()
    def rollback(self): self.session.rollback()