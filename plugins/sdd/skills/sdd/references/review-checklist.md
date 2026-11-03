# Checklist de revisión de un cambio SDD

Elige las filas según el diff; no conviertas cada fila en un hallazgo. Ocho filas.

| Área | Qué comprobar |
|---|---|
| Trazabilidad | Cada REQ de `ADDED` y `MODIFIED` tiene al menos un test que lo nombra (en el nombre o en una línea, como diga el paquete de lenguaje); ningún test nombra un REQ de `REMOVED`. `sdd.py coverage` no lista ninguno de los del delta |
| Alcance | El diff no implementa nada que no esté en el delta; lo que sobra se quita o se propone como ampliación del delta. En una PR `self-service`, ningún fichero fuera de `selfService` (`sdd.py selfservice`) |
| Spec | `spec.md` no cambia en la PR del cambio (lo cambia la fusión); el delta pasa `sdd.py check` y tiene `approved_by` |
| Compatibilidad | Un `MODIFIED` que cambia un contrato (ruta, formato, código de respuesta, mensaje publicado) lo dice en "Por qué" y tiene el test del comportamiento antiguo eliminado a propósito |
| Datos | Si un requisito cambia el esquema de datos: migración revisada (reversible, sin pérdida), datos históricos contemplados |
| Decisiones | Las decisiones del spec siguen siendo ciertas tras el cambio; si no, el delta debe actualizarlas en la fusión |
| Commits | Cada commit de implementación cita su REQ y lleva `Refs: PBI-<id>` (o la clave de Jira); los índices van regenerados en los commits que tocan `docs/features/` |
| Diseño | Ninguna señal encendida de [principles.md](principles.md) (responsabilidad única, dependencias hacia dentro, sin duplicar conocimiento, errores explícitos, idempotencia en consumidores); se cita el principio y la señal, no una preferencia de estilo |
