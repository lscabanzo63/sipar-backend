from datetime import datetime
import calendar

try:
    from dateutil.relativedelta import relativedelta  
    _HAS_DATEUTIL = True
except Exception:
    _HAS_DATEUTIL = False

def _add_months_fallback(dt: datetime, months: int) -> datetime:
    """Suma meses manteniendo el día; si no existe, usa último día del mes (fallback sin dateutil)."""
    y = dt.year + (dt.month - 1 + months) // 12
    m = (dt.month - 1 + months) % 12 + 1
    last_day = calendar.monthrange(y, m)[1]
    day = min(dt.day, last_day)
    return dt.replace(year=y, month=m, day=day)

def add_months_keep_day(dt: datetime, months: int) -> datetime:
    if _HAS_DATEUTIL:
        target = dt + relativedelta(months=months)
        last_day = calendar.monthrange(target.year, target.month)[1]
        day = min(dt.day, last_day)
        return target.replace(day=day)
    return _add_months_fallback(dt, months)

def fechas_ciclo(fecha_inicio: datetime, periodicidad: str) -> list[datetime]:
    per = periodicidad.upper().strip()
    jumps = {
        'TRIMESTRAL': [0, 3, 6, 9],
        'CUATRIMESTRAL': [0, 4, 8],
        'SEMESTRAL': [0, 6],
    }
    if per not in jumps:
        raise ValueError(f"Periodicidad desconocida: {periodicidad}")
    return [add_months_keep_day(fecha_inicio, m) for m in jumps[per]]