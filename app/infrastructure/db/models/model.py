from typing import Optional
import datetime

from sqlalchemy import Boolean, Date, ForeignKeyConstraint, Integer, PrimaryKeyConstraint, String, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Departamento(Base):
    __tablename__ = 'departamento'
    __table_args__ = (
        PrimaryKeyConstraint('id_departamento', name='departamento_pkey'),
    )

    id_departamento: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_departamento: Mapped[str] = mapped_column(String(100), nullable=False)

    ciudad: Mapped[list['Ciudad']] = relationship('Ciudad', back_populates='departamento')


class EstadoApartamento(Base):
    __tablename__ = 'estado_apartamento'
    __table_args__ = (
        PrimaryKeyConstraint('id_estado_apartamento', name='estado_apartamento_pkey'),
    )

    id_estado_apartamento: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_estado: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion_estado: Mapped[Optional[str]] = mapped_column(String(255))

    apartamento: Mapped[list['Apartamento']] = relationship('Apartamento', back_populates='estado_apartamento')


class Incidente(Base):
    __tablename__ = 'incidente'
    __table_args__ = (
        PrimaryKeyConstraint('id_incidente', name='incidente_pkey'),
    )

    id_incidente: Mapped[int] = mapped_column(Integer, primary_key=True)
    descripcion_incidente: Mapped[str] = mapped_column(String(255), nullable=False)


class Norma(Base):
    __tablename__ = 'norma'
    __table_args__ = (
        PrimaryKeyConstraint('id_norma', name='norma_pkey'),
    )

    id_norma: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_norma: Mapped[str] = mapped_column(String(100), nullable=False)
    sorteo_id: Mapped[Optional[int]] = mapped_column(Integer)

    usuario: Mapped[list['Usuario']] = relationship('Usuario', back_populates='administracion')
    sorteo: Mapped[list['Sorteo']] = relationship('Sorteo', back_populates='norma')


class Parqueadero(Base):
    __tablename__ = 'parqueadero'
    __table_args__ = (
        PrimaryKeyConstraint('id_parqueadero', name='parqueadero_pkey'),
    )

    id_parqueadero: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero_parqueadero: Mapped[int] = mapped_column(Integer, nullable=False)

    apartamento: Mapped[list['Apartamento']] = relationship('Apartamento', back_populates='parqueadero')


class Permiso(Base):
    __tablename__ = 'permiso'
    __table_args__ = (
        PrimaryKeyConstraint('id_permiso', name='permiso_pkey'),
    )

    id_permiso: Mapped[int] = mapped_column(Integer, primary_key=True)
    descripcion_permiso: Mapped[str] = mapped_column(String(255), nullable=False)

    rol_permiso: Mapped[list['RolPermiso']] = relationship('RolPermiso', back_populates='permiso')


class TipoTransporte(Base):
    __tablename__ = 'tipo_transporte'
    __table_args__ = (
        PrimaryKeyConstraint('id_tipo_transporte', name='tipo_transporte_pkey'),
    )

    id_tipo_transporte: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_tipo: Mapped[str] = mapped_column(String(50), nullable=False)

    transporte: Mapped[list['Transporte']] = relationship('Transporte', back_populates='tipo_transporte')


class TipoUsuario(Base):
    __tablename__ = 'tipo_usuario'
    __table_args__ = (
        PrimaryKeyConstraint('id_tipo_usuario', name='tipo_usuario_pkey'),
    )

    id_tipo_usuario: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_tipo_usuario: Mapped[str] = mapped_column(String(50), nullable=False)

    rol_permiso: Mapped[list['RolPermiso']] = relationship('RolPermiso', back_populates='tipo_usuario')
    usuario: Mapped[list['Usuario']] = relationship('Usuario', back_populates='tipo_usuario')


class Ciudad(Base):
    __tablename__ = 'ciudad'
    __table_args__ = (
        ForeignKeyConstraint(['departamento_id'], ['departamento.id_departamento'], name='ciudad_departamento_id_fkey'),
        PrimaryKeyConstraint('id_ciudad', name='ciudad_pkey')
    )

    id_ciudad: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_ciudad: Mapped[str] = mapped_column(String(100), nullable=False)
    departamento_id: Mapped[Optional[int]] = mapped_column(Integer)

    departamento: Mapped[Optional['Departamento']] = relationship('Departamento', back_populates='ciudad')
    conjunto_residencial: Mapped[list['ConjuntoResidencial']] = relationship('ConjuntoResidencial', back_populates='ciudad')


class RolPermiso(Base):
    __tablename__ = 'rol_permiso'
    __table_args__ = (
        ForeignKeyConstraint(['permiso_id'], ['permiso.id_permiso'], name='rol_permiso_permiso_id_fkey'),
        ForeignKeyConstraint(['tipo_usuario_id'], ['tipo_usuario.id_tipo_usuario'], name='rol_permiso_tipo_usuario_id_fkey'),
        PrimaryKeyConstraint('id_rol_permiso', name='rol_permiso_pkey')
    )

    id_rol_permiso: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo_usuario_id: Mapped[Optional[int]] = mapped_column(Integer)
    permiso_id: Mapped[Optional[int]] = mapped_column(Integer)

    permiso: Mapped[Optional['Permiso']] = relationship('Permiso', back_populates='rol_permiso')
    tipo_usuario: Mapped[Optional['TipoUsuario']] = relationship('TipoUsuario', back_populates='rol_permiso')
    usuario: Mapped[list['Usuario']] = relationship('Usuario', back_populates='rol_permiso')


class ConjuntoResidencial(Base):
    __tablename__ = 'conjunto_residencial'
    __table_args__ = (
        ForeignKeyConstraint(['ciudad_id'], ['ciudad.id_ciudad'], name='conjunto_residencial_ciudad_id_fkey'),
        PrimaryKeyConstraint('id_conjunto_residencial', name='conjunto_residencial_pkey')
    )

    id_conjunto_residencial: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_conjunto: Mapped[str] = mapped_column(String(100), nullable=False)
    direccion_conjunto: Mapped[Optional[str]] = mapped_column(String(255))
    numero_torres: Mapped[Optional[int]] = mapped_column(Integer)
    numero_apartamentos: Mapped[Optional[int]] = mapped_column(Integer)
    ciudad_id: Mapped[Optional[int]] = mapped_column(Integer)
    email_contacto: Mapped[Optional[str]] = mapped_column(String(255))
    telefono_contacto: Mapped[Optional[str]] = mapped_column(String(15))
    numero_parqueaderos: Mapped[Optional[int]] = mapped_column(Integer)

    ciudad: Mapped[Optional['Ciudad']] = relationship('Ciudad', back_populates='conjunto_residencial')
    apartamento: Mapped[list['Apartamento']] = relationship('Apartamento', back_populates='conjunto_residencial')
    sorteo: Mapped[list['Sorteo']] = relationship('Sorteo', back_populates='conjunto_residencial')


class Usuario(Base):
    __tablename__ = 'usuario'
    __table_args__ = (
        ForeignKeyConstraint(['administracion_id'], ['norma.id_norma'], name='usuario_administracion_id_fkey'),
        ForeignKeyConstraint(['rol_permiso_id'], ['rol_permiso.id_rol_permiso'], name='usuario_rol_permiso_id_fkey'),
        ForeignKeyConstraint(['tipo_usuario_id'], ['tipo_usuario.id_tipo_usuario'], name='usuario_tipo_usuario_id_fkey'),
        PrimaryKeyConstraint('id_usuario', name='usuario_pkey')
    )

    id_usuario: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    contrasena: Mapped[str] = mapped_column(String(255), nullable=False)
    first_time: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    telefono: Mapped[Optional[str]] = mapped_column(String(15))
    tipo_usuario_id: Mapped[Optional[int]] = mapped_column(Integer)
    rol_permiso_id: Mapped[Optional[int]] = mapped_column(Integer)
    administracion_id: Mapped[Optional[int]] = mapped_column(Integer)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    documento: Mapped[Optional[str]] = mapped_column(String(30))

    administracion: Mapped[Optional['Norma']] = relationship('Norma', back_populates='usuario')
    rol_permiso: Mapped[Optional['RolPermiso']] = relationship('RolPermiso', back_populates='usuario')
    tipo_usuario: Mapped[Optional['TipoUsuario']] = relationship('TipoUsuario', back_populates='usuario')
    apartamento: Mapped[list['Apartamento']] = relationship('Apartamento', back_populates='usuario')
    sorteo: Mapped[list['Sorteo']] = relationship('Sorteo', back_populates='usuario')
    usuario_incidente: Mapped[list['UsuarioIncidente']] = relationship('UsuarioIncidente', back_populates='usuario')


class Apartamento(Base):
    __tablename__ = 'apartamento'
    __table_args__ = (
        ForeignKeyConstraint(['conjunto_residencial_id'], ['conjunto_residencial.id_conjunto_residencial'], name='apartamento_conjunto_residencial_id_fkey'),
        ForeignKeyConstraint(['estado_apartamento_id'], ['estado_apartamento.id_estado_apartamento'], name='apartamento_estado_apartamento_id_fkey'),
        ForeignKeyConstraint(['parqueadero_id'], ['parqueadero.id_parqueadero'], name='apartamento_parqueadero_id_fkey'),
        ForeignKeyConstraint(['usuario_id'], ['usuario.id_usuario'], name='apartamento_usuario_id_fkey'),
        PrimaryKeyConstraint('id_apartamento', name='apartamento_pkey')
    )

    id_apartamento: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero_apartamento: Mapped[int] = mapped_column(Integer, nullable=False)
    usuario_id: Mapped[Optional[int]] = mapped_column(Integer)
    estado_apartamento_id: Mapped[Optional[int]] = mapped_column(Integer)
    conjunto_residencial_id: Mapped[Optional[int]] = mapped_column(Integer)
    parqueadero_id: Mapped[Optional[int]] = mapped_column(Integer)
    nombre_torre: Mapped[Optional[str]] = mapped_column(String(50))
    piso: Mapped[Optional[int]] = mapped_column(Integer)

    conjunto_residencial: Mapped[Optional['ConjuntoResidencial']] = relationship('ConjuntoResidencial', back_populates='apartamento')
    estado_apartamento: Mapped[Optional['EstadoApartamento']] = relationship('EstadoApartamento', back_populates='apartamento')
    parqueadero: Mapped[Optional['Parqueadero']] = relationship('Parqueadero', back_populates='apartamento')
    usuario: Mapped[Optional['Usuario']] = relationship('Usuario', back_populates='apartamento')


class Sorteo(Base):
    __tablename__ = 'sorteo'
    __table_args__ = (
        ForeignKeyConstraint(['conjunto_residencial_id'], ['conjunto_residencial.id_conjunto_residencial'], name='sorteo_conjunto_residencial_id_fkey'),
        ForeignKeyConstraint(['norma_id'], ['norma.id_norma'], name='sorteo_norma_id_fkey'),
        ForeignKeyConstraint(['usuario_id'], ['usuario.id_usuario'], name='sorteo_usuario_id_fkey'),
        PrimaryKeyConstraint('id_sorteo', name='sorteo_pkey')
    )

    id_sorteo: Mapped[int] = mapped_column(Integer, primary_key=True)
    fecha_sorteo: Mapped[Optional[datetime.date]] = mapped_column(Date)
    resultado_sorteo: Mapped[Optional[str]] = mapped_column(String(255))
    usuario_id: Mapped[Optional[int]] = mapped_column(Integer)
    norma_id: Mapped[Optional[int]] = mapped_column(Integer)
    conjunto_residencial_id: Mapped[Optional[int]] = mapped_column(Integer)
    parqueadero_id: Mapped[Optional[int]] = mapped_column(Integer)

    conjunto_residencial: Mapped[Optional['ConjuntoResidencial']] = relationship('ConjuntoResidencial', back_populates='sorteo')
    norma: Mapped[Optional['Norma']] = relationship('Norma', back_populates='sorteo')
    usuario: Mapped[Optional['Usuario']] = relationship('Usuario', back_populates='sorteo')
    transporte: Mapped[list['Transporte']] = relationship('Transporte', back_populates='sorteo')


class UsuarioIncidente(Base):
    __tablename__ = 'usuario_incidente'
    __table_args__ = (
        ForeignKeyConstraint(['usuario_id'], ['usuario.id_usuario'], name='usuario_incidente_usuario_id_fkey'),
        PrimaryKeyConstraint('id_usuario_incidente', name='usuario_incidente_pkey')
    )

    id_usuario_incidente: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(Integer)
    incidente_id: Mapped[Optional[int]] = mapped_column(Integer)

    usuario: Mapped[Optional['Usuario']] = relationship('Usuario', back_populates='usuario_incidente')


class Transporte(Base):
    __tablename__ = 'transporte'
    __table_args__ = (
        ForeignKeyConstraint(['sorteo_id'], ['sorteo.id_sorteo'], name='transporte_sorteo_id_fkey'),
        ForeignKeyConstraint(['tipo_transporte_id'], ['tipo_transporte.id_tipo_transporte'], name='transporte_tipo_transporte_id_fkey'),
        PrimaryKeyConstraint('id_transporte', name='transporte_pkey')
    )

    id_transporte: Mapped[int] = mapped_column(Integer, primary_key=True)
    placa: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha_resultado: Mapped[Optional[datetime.date]] = mapped_column(Date)
    soat: Mapped[Optional[str]] = mapped_column(String(50))
    tecnomecanica: Mapped[Optional[str]] = mapped_column(String(50))
    sorteo_id: Mapped[Optional[int]] = mapped_column(Integer)
    tipo_transporte_id: Mapped[Optional[int]] = mapped_column(Integer)

    sorteo: Mapped[Optional['Sorteo']] = relationship('Sorteo', back_populates='transporte')
    tipo_transporte: Mapped[Optional['TipoTransporte']] = relationship('TipoTransporte', back_populates='transporte')
