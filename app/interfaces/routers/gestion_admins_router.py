from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, update, func
from typing import List

from app.core.security.deps import roles_required
from app.infrastructure.db.database import get_db
from app.infrastructure.db.models.model import (
    Usuario, TipoUsuario, ConjuntoResidencial, Apartamento, Ciudad
)
from app.core.security.passwords import generar_password, hash_password
from app.application.common.use_case.schemas.gestion_admin_schemas import (
    CrearAdminRequest, AdminItemOut, ToggleEstadoRequest, ModificarAdminRequest
)

router = APIRouter(
    prefix="/api/v1/gestion/admins",
    tags=["Gestión de Administradores"],
    dependencies=[Depends(roles_required("gestor"))],
)

def _get_ciudad_id(db: Session, nombre: str) -> int:
    cid = db.execute(
        select(Ciudad.id_ciudad).where(
            func.lower(func.trim(Ciudad.nombre_ciudad)) == func.lower(func.trim(nombre))
        )
    ).scalar_one_or_none()

    if cid is None:
        raise HTTPException(
            status_code=404,
            detail=f"Ciudad '{nombre}' no existe en la base de datos"
        )
    return cid


def _get_tipo_admin_id(db: Session) -> int:
    tid = db.execute(
        select(TipoUsuario.id_tipo_usuario).where(
            func.lower(func.trim(TipoUsuario.nombre_tipo_usuario)) == func.lower("administrador")
        )
    ).scalar_one_or_none()

    if tid is None:
        raise HTTPException(
            status_code=500,
            detail="Tipo de usuario 'administrador' no está configurado en la base de datos"
        )
    return tid

@router.post("", status_code=status.HTTP_201_CREATED)
def crear_admin(req: CrearAdminRequest, db: Session = Depends(get_db)):
    try:
        # Validar email único
        exists = db.execute(
            select(func.count()).select_from(Usuario).where(Usuario.email == req.admin.email)
        ).scalar()
        if exists:
            raise HTTPException(status_code=409, detail="El email del administrador ya existe")

        # 1) Crear usuario con contraseña aleatoria
        tipo_admin_id = _get_tipo_admin_id(db)
        plain_password = generar_password()  # contraseña temporal
        password_hash = hash_password(plain_password)

        new_user_id = db.execute(
            insert(Usuario).values(
                nombre=req.admin.nombres,
                apellidos=req.admin.apellidos,
                telefono=req.admin.telefono,
                contrasena=password_hash,
                tipo_usuario_id=tipo_admin_id,
                first_time=True,
                email=req.admin.email,
                documento=req.admin.documento,
                administracion=False,
                estado=True,
            ).returning(Usuario.id_usuario)
        ).scalar_one()

        # 2) Crear conjunto residencial
        ciudad_id = _get_ciudad_id(db, req.conjunto.ciudad)
        new_conjunto_id = db.execute(
            insert(ConjuntoResidencial).values(
                nombre_conjunto=req.conjunto.nombre,
                direccion_conjunto=req.conjunto.direccion,
                numero_torres=req.conjunto.numero_torres,
                numero_apartamentos=req.conjunto.numero_apartamentos,
                ciudad_id=ciudad_id,
                email_contacto=req.conjunto.email_conjunto,
                telefono_contacto=req.conjunto.telefono_conjunto,
                numero_parqueaderos=req.conjunto.numero_parqueaderos,
            ).returning(ConjuntoResidencial.id_conjunto_residencial)
        ).scalar_one()

        # 3) Crear apartamento placeholder
        db.execute(
            insert(Apartamento).values(
                usuario_id=new_user_id,
                conjunto_residencial_id=new_conjunto_id,
            )
        )

        db.commit()

        # Devolver también la contraseña generada
        return {
            "status": "created",
            "id_usuario": new_user_id,
            "id_conjunto": new_conjunto_id,
            "password_temporal": plain_password
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear administrador: {e}")


@router.get("", response_model=List[AdminItemOut])
def listar_admins(db: Session = Depends(get_db)):
    # Traer todos los usuarios ADMINISTRADOR con su conjunto (vía apartamento)
    tipo_admin_id = db.execute(
        select(TipoUsuario.id_tipo_usuario).where(TipoUsuario.nombre_tipo_usuario == "administrador")
    ).scalar_one_or_none()
    if tipo_admin_id is None:
        return []

    # join: usuario -> apartamento -> conjunto_residencial
    rows = db.execute(
        select(
            Usuario.id_usuario,
            Usuario.nombre,
            Usuario.apellidos,
            Usuario.email,
            Usuario.telefono,
            ConjuntoResidencial.nombre_conjunto,
            Usuario.estado,
        )
        .join(Apartamento, Apartamento.usuario_id == Usuario.id_usuario, isouter=True)
        .join(ConjuntoResidencial, ConjuntoResidencial.id_conjunto_residencial == Apartamento.conjunto_residencial_id, isouter=True)
        .where(Usuario.tipo_usuario_id == tipo_admin_id)
        .order_by(Usuario.id_usuario.desc())
    ).all()

    return [
        AdminItemOut(
            id_usuario=r[0],
            nombres=r[1],
            apellidos=r[2],
            email=r[3],
            telefono=r[4],
            conjunto=r[5] or "(sin conjunto)",
            estado=bool(r[6]),
        )
        for r in rows
    ]

@router.patch("/{id_usuario}/estado")
def toggle_estado_admin(id_usuario: int, req: ToggleEstadoRequest, db: Session = Depends(get_db)):
    # Accion: Bloqueo -> estado=false;  Desbloqueo -> estado=true
    target = db.execute(select(Usuario).where(Usuario.id_usuario == id_usuario)).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    new_state = True if req.accion == "Desbloqueo" else False
    db.execute(update(Usuario).where(Usuario.id_usuario == id_usuario).values(estado=new_state))
    db.commit()
    return {"status": "ok", "estado": new_state}

@router.patch("/{id_usuario}")
def modificar_admin(id_usuario: int, req: ModificarAdminRequest, db: Session = Depends(get_db)):
    target = db.execute(select(Usuario).where(Usuario.id_usuario == id_usuario)).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Validación de email duplicado si lo cambian
    if req.email and req.email != (target.email or ""):
        exists = db.execute(select(func.count()).select_from(Usuario).where(Usuario.email == req.email)).scalar()
        if exists:
            raise HTTPException(status_code=409, detail="Email ya está en uso")

    update_values = {}
    if req.nombres is not None:   update_values["nombre"] = req.nombres
    if req.apellidos is not None: update_values["apellidos"] = req.apellidos
    if req.email is not None:     update_values["email"] = req.email
    if req.telefono is not None:  update_values["telefono"] = req.telefono
    if req.documento is not None: update_values["documento"] = req.documento

    if not update_values:
        return {"status": "noop"}

    db.execute(update(Usuario).where(Usuario.id_usuario == id_usuario).values(**update_values))
    db.commit()
    return {"status": "ok", "id_usuario": id_usuario}
