# Principios que no dependen del lenguaje

Cada lenguaje y cada repo tienen sus reglas (están en el paquete de lenguaje activo, `references/languages/` o `docs/sdd/languages/`, y en el `AGENTS.md` del repo). Esto es lo que se exige igual en cualquier lenguaje, y lo que el revisor mira además del checklist del delta. Se aplica al implementar; no se añade por aplicarlo. Las señales están escritas sin nombres de librerías a propósito; la tabla final de cada paquete de lenguaje las traduce a lo que se ve en ese ecosistema.

| Principio | Qué significa aquí | Señal de que se está rompiendo |
|---|---|---|
| **Responsabilidad única** (S) | Una clase o módulo cambia por un solo motivo; un handler hace una cosa | Un fichero que toca persistencia, mensajería y validación a la vez; un "manager", "helper" o "utils" que crece con cada PBI |
| **Abierto/cerrado** (O) | Añadir un caso no edita los existentes: nueva estrategia, nuevo consumidor, nuevo requisito | Un `switch` o cadena de `if` sobre un tipo que crece con cada feature |
| **Sustitución de Liskov** (L) | Lo que acepta la abstracción acepta cualquiera de sus implementaciones sin sorpresas | Una implementación que lanza "no soportado" o ignora parámetros del contrato |
| **Segregación de interfaces** (I) | Interfaces pequeñas por quien las consume, no por quien las implementa | Un repositorio con veinte métodos del que cada consumidor usa dos |
| **Inversión de dependencias** (D) | El dominio y la aplicación definen las abstracciones; la infraestructura las implementa | Importar el ORM, el cliente HTTP o un SDK dentro del dominio; construir un cliente externo dentro de un handler |
| **Lo mínimo que cumple el requisito** | Se implementa el GIVEN/WHEN/THEN aprobado, no el que podría venir | Parámetros "por si acaso", opciones sin consumidor, abstracciones con una sola implementación |
| **Sin duplicar conocimiento** | Una regla de negocio vive en un sitio; el mismo dato no se calcula en dos | Dos validaciones del mismo campo con mensajes distintos; una constante repetida en API y dominio |
| **Errores explícitos** | Los casos de negocio son resultados, no excepciones; las excepciones son para lo inesperado y no se tragan | `catch` vacío o que solo loguea; usar excepciones para "no encontrado" o "no válido" |
| **Límites claros** | Cada capa habla solo con la contigua; los contratos entre servicios son los mensajes del spec (`Publica:` / `Consume:`) | Un servicio leyendo la base de datos de otro; un DTO de la API filtrándose al dominio |
| **Nombres que dicen qué** | El nombre de clase, método y test hace innecesario el comentario; los nombres del flujo (features, requisitos, ramas, commits, mensajes) siguen la tabla de [format.md](format.md#nombres) | `process`, `handle2`, `data`, `tmp`; un comentario que explica lo que el nombre debería; una rama o commit sin el id |
| **Tests que prueban el requisito** | Un test por GIVEN/WHEN/THEN, con el id del requisito; prueba comportamiento observable, no la implementación | Tests que fallan al renombrar algo privado; tests sin aserción sobre el resultado |
| **Idempotencia donde hay mensajes** | Un consumidor que recibe dos veces el mismo evento deja el sistema igual que si lo hubiera recibido una | Un consumidor que inserta sin comprobar, o que activa algo ya activo lanzando error |

Cómo se usa: al implementar un requisito, si el código resultante enciende alguna señal, se corrige antes del commit. Al revisar, el revisor cita el principio y la señal, no una preferencia de estilo. Lo que es estilo (formato, orden de imports, convenciones de nombres del lenguaje) va al paquete de lenguaje y al `AGENTS.md` del repo, y lo aplica el formateador, no una persona.
