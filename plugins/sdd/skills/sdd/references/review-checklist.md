# Checklist de revisión de un cambio SDD

Elige las filas según el diff; no conviertas cada fila en un hallazgo.

| Área | Qué comprobar |
|---|---|
| Trazabilidad | Cada REQ de `ADDED` y `MODIFIED` tiene al menos un test que lo nombra (en el nombre o en una línea); ningún test nombra un REQ de `REMOVED` |
| Alcance | El diff no implementa nada que no esté en el delta; lo que sobra se quita o se propone como ampliación del delta |
| Spec | `spec.md` no cambia en la PR del cambio (lo cambia la fusión); el delta pasa `sdd.py check` |
| Compatibilidad | Un `MODIFIED` que cambia un contrato (ruta, formato, código de respuesta) lo dice en "Por qué" y tiene test del comportamiento antiguo eliminado a propósito |
| Datos | Si un requisito toca persistencia: migración o `EnsureCreated` revisado, datos históricos contemplados |
| Decisiones | Las decisiones del spec siguen siendo ciertas tras el cambio; si no, el delta debe actualizarlas en la fusión |
| Commits | Cada commit de implementación cita su REQ y lleva `Refs: PBI-<id>` |
