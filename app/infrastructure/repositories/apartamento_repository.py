from sqlalchemy import text
from sqlalchemy.engine import Engine
from typing import List, Tuple


class ApartamentoRepo:
    def __init__(self, engine: Engine): self.engine = engine

    def capacidad_conjunto(self, conjunto_id:int) -> int:
        from sqlalchemy import text
        with self.engine.begin() as con:
            r = con.execute(text("SELECT numero_parqueaderos FROM conjunto_residencial WHERE id_conjunto_residencial=:c"),
                            {"c":conjunto_id}).first()
            return int(r[0]) if r else 0

    def asignar_parqueaderos(self, conjunto_id:int, usuarios_ordenados: List[int], cupo:int) -> List[Tuple[int,int]]:
        asignaciones=[]
        with self.engine.begin() as con:
            take = usuarios_ordenados[:cupo]
            slot=1
            for uid in take:
                con.execute(text("""
                    UPDATE apartamento SET numero_parqueadero=:np
                    WHERE usuario_id=:uid AND conjunto_residencial_id=:cid
                """), {"np":slot, "uid":uid, "cid":conjunto_id})
                asignaciones.append((uid, slot))
                slot += 1
        return asignaciones