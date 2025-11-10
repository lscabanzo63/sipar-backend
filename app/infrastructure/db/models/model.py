from typing import Optional
import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKeyConstraint, Index, Integer, PrimaryKeyConstraint, String, Text, UniqueConstraint, text
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


class Norma(Base):
    __tablename__ = 'norma'
    __table_args__ = (
        PrimaryKeyConstraint('id_norma', name='norma_pkey'),
    )

    id_norma: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_norma: Mapped[str] = mapped_column(String(100), nullable=False)

    sorteo_norma: Mapped[list['SorteoNorma']] = relationship('SorteoNorma', back_populates='norma')


class TipoUsuario(Base):
    __tablename__ = 'tipo_usuario'
    __table_args__ = (
        PrimaryKeyConstraint('id_tipo_usuario', name='tipo_usuario_pkey'),
    )

    id_tipo_usuario: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_tipo_usuario: Mapped[str] = mapped_column(String(50), nullable=False)

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


class Usuario(Base):
    __tablename__ = 'usuario'
    __table_args__ = (
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
    email: Mapped[Optional[str]] = mapped_column(String(255))
    documento: Mapped[Optional[str]] = mapped_column(String(30))
    administracion: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))

    tipo_usuario: Mapped[Optional['TipoUsuario']] = relationship('TipoUsuario', back_populates='usuario')
    apartamento: Mapped[list['Apartamento']] = relationship('Apartamento', back_populates='usuario')
    resultado_sorteo_detalle: Mapped[list['ResultadoSorteoDetalle']] = relationship('ResultadoSorteoDetalle', back_populates='usuario')


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
    sorteo: Mapped[Optional['Sorteo']] = relationship('Sorteo', uselist=False, back_populates='conjunto_residencial')


class Apartamento(Base):
    __tablename__ = 'apartamento'
    __table_args__ = (
        ForeignKeyConstraint(['conjunto_residencial_id'], ['conjunto_residencial.id_conjunto_residencial'], name='apartamento_conjunto_residencial_id_fkey'),
        ForeignKeyConstraint(['estado_apartamento_id'], ['estado_apartamento.id_estado_apartamento'], name='apartamento_estado_apartamento_id_fkey'),
        ForeignKeyConstraint(['usuario_id'], ['usuario.id_usuario'], name='apartamento_usuario_id_fkey'),
        PrimaryKeyConstraint('id_apartamento', name='apartamento_pkey')
    )

    id_apartamento: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero_apartamento: Mapped[Optional[int]] = mapped_column(Integer)
    usuario_id: Mapped[Optional[int]] = mapped_column(Integer)
    estado_apartamento_id: Mapped[Optional[int]] = mapped_column(Integer)
    conjunto_residencial_id: Mapped[Optional[int]] = mapped_column(Integer)
    nombre_torre: Mapped[Optional[str]] = mapped_column(String(50))
    piso: Mapped[Optional[int]] = mapped_column(Integer)
    numero_parqueadero: Mapped[Optional[int]] = mapped_column(Integer)

    conjunto_residencial: Mapped[Optional['ConjuntoResidencial']] = relationship('ConjuntoResidencial', back_populates='apartamento')
    estado_apartamento: Mapped[Optional['EstadoApartamento']] = relationship('EstadoApartamento', back_populates='apartamento')
    usuario: Mapped[Optional['Usuario']] = relationship('Usuario', back_populates='apartamento')


class Sorteo(Base):
    __tablename__ = 'sorteo'
    __table_args__ = (
        ForeignKeyConstraint(['conjunto_residencial_id'], ['conjunto_residencial.id_conjunto_residencial'], name='sorteo_conjunto_residencial_id_fkey'),
        PrimaryKeyConstraint('id_sorteo', name='sorteo_pkey'),
        UniqueConstraint('conjunto_residencial_id', name='uniq_sorteo_conjunto')
    )

    id_sorteo: Mapped[int] = mapped_column(Integer, primary_key=True)
    sequence_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    conjunto_residencial_id: Mapped[Optional[int]] = mapped_column(Integer)
    periodicidad: Mapped[Optional[str]] = mapped_column(Enum('TRIMESTRAL', 'CUATRIMESTRAL', 'SEMESTRAL', name='periodicidad_enum'))

    conjunto_residencial: Mapped[Optional['ConjuntoResidencial']] = relationship('ConjuntoResidencial', back_populates='sorteo')
    sorteo_fecha: Mapped[list['SorteoFecha']] = relationship('SorteoFecha', back_populates='sorteo')
    sorteo_norma: Mapped[list['SorteoNorma']] = relationship('SorteoNorma', back_populates='sorteo')
    resultado_sorteo: Mapped[list['ResultadoSorteo']] = relationship('ResultadoSorteo', back_populates='sorteo')


class SorteoFecha(Base):
    __tablename__ = 'sorteo_fecha'
    __table_args__ = (
        ForeignKeyConstraint(['sorteo_id'], ['sorteo.id_sorteo'], ondelete='CASCADE', name='sorteo_fecha_sorteo_id_fkey'),
        PrimaryKeyConstraint('id_sorteo_fecha', name='sorteo_fecha_pkey'),
        UniqueConstraint('sorteo_id', 'fecha', name='sorteo_fecha_unq')
    )

    id_sorteo_fecha: Mapped[int] = mapped_column(Integer, primary_key=True)
    sorteo_id: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))

    sorteo: Mapped['Sorteo'] = relationship('Sorteo', back_populates='sorteo_fecha')
    resultado_sorteo: Mapped[list['ResultadoSorteo']] = relationship('ResultadoSorteo', back_populates='sorteo_fecha')


class SorteoNorma(Base):
    __tablename__ = 'sorteo_norma'
    __table_args__ = (
        ForeignKeyConstraint(['norma_id'], ['norma.id_norma'], ondelete='CASCADE', name='sorteo_norma_norma_id_fkey'),
        ForeignKeyConstraint(['sorteo_id'], ['sorteo.id_sorteo'], ondelete='CASCADE', name='sorteo_norma_sorteo_id_fkey'),
        PrimaryKeyConstraint('sorteo_id', 'norma_id', name='sorteo_norma_pkey'),
        Index('sorteo_norma_norma_idx', 'norma_id'),
        Index('sorteo_norma_sorteo_idx', 'sorteo_id')
    )

    sorteo_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    norma_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parametro: Mapped[Optional[str]] = mapped_column(Text)

    norma: Mapped['Norma'] = relationship('Norma', back_populates='sorteo_norma')
    sorteo: Mapped['Sorteo'] = relationship('Sorteo', back_populates='sorteo_norma')


class ResultadoSorteo(Base):
    __tablename__ = 'resultado_sorteo'
    __table_args__ = (
        ForeignKeyConstraint(['sorteo_fecha_id'], ['sorteo_fecha.id_sorteo_fecha'], ondelete='RESTRICT', name='resultado_sorteo_sorteo_fecha_id_fkey'),
        ForeignKeyConstraint(['sorteo_id'], ['sorteo.id_sorteo'], ondelete='CASCADE', name='resultado_sorteo_sorteo_id_fkey'),
        PrimaryKeyConstraint('id_resultado_sorteo', name='resultado_sorteo_pkey'),
        Index('idx_resultado_sorteo_sorteo_id', 'sorteo_id'),
        Index('uq_resultado_sorteo_por_fecha', 'sorteo_fecha_id')
    )

    id_resultado_sorteo: Mapped[int] = mapped_column(Integer, primary_key=True)
    sorteo_id: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    sorteo_fecha_id: Mapped[Optional[int]] = mapped_column(Integer)

    sorteo_fecha: Mapped[Optional['SorteoFecha']] = relationship('SorteoFecha', back_populates='resultado_sorteo')
    sorteo: Mapped['Sorteo'] = relationship('Sorteo', back_populates='resultado_sorteo')
    resultado_sorteo_detalle: Mapped[list['ResultadoSorteoDetalle']] = relationship('ResultadoSorteoDetalle', back_populates='resultado_sorteo')


class ResultadoSorteoDetalle(Base):
    __tablename__ = 'resultado_sorteo_detalle'
    __table_args__ = (
        ForeignKeyConstraint(['resultado_sorteo_id'], ['resultado_sorteo.id_resultado_sorteo'], ondelete='CASCADE', name='resultado_sorteo_detalle_resultado_sorteo_id_fkey'),
        ForeignKeyConstraint(['usuario_id'], ['usuario.id_usuario'], ondelete='RESTRICT', name='resultado_sorteo_detalle_usuario_id_fkey'),
        PrimaryKeyConstraint('id_resultado_sorteo_detalle', name='resultado_sorteo_detalle_pkey')
    )

    id_resultado_sorteo_detalle: Mapped[int] = mapped_column(Integer, primary_key=True)
    resultado_sorteo_id: Mapped[int] = mapped_column(Integer, nullable=False)
    usuario_id: Mapped[int] = mapped_column(Integer, nullable=False)
    numero_parqueadero: Mapped[Optional[int]] = mapped_column(Integer)

    resultado_sorteo: Mapped['ResultadoSorteo'] = relationship('ResultadoSorteo', back_populates='resultado_sorteo_detalle')
    usuario: Mapped['Usuario'] = relationship('Usuario', back_populates='resultado_sorteo_detalle')
