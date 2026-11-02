---
name: masstransit-saga
description: Cómo montar una saga (máquina de estados) con MassTransit 8 en .NET: MassTransitStateMachine, Schedule para plazos, Ignore y OnMissingInstance, repositorio EF Core, transporte SQL Server, RabbitMQ o Azure Service Bus, y cómo probarla con el test harness. Usar al crear o tocar una saga, un proceso que espera a una persona o a un plazo, o al elegir transporte ("necesito una saga", "proceso con timeout", "state machine de MassTransit", "test harness de MassTransit").
---

Una saga de MassTransit es una máquina de estados con instancia persistida: una fila por proceso en curso que avanza con cada mensaje y se borra al terminar. Ejemplo completo, probado y documentado: [MassTransit.Saga.Demo](https://github.com/goguiGit/MassTransit.Saga.Demo) (registro con confirmación de email, dos servicios, tres transportes). Lee su README antes de inventar.

## Versión y paquetes

MassTransit **8.x** (`8.5.x`); la 9 pasó a licencia comercial. Paquetes: `MassTransit`, `MassTransit.EntityFrameworkCore` (repositorio de sagas), y el transporte: `MassTransit.SqlTransport.SqlServer`, `MassTransit.RabbitMQ` o `MassTransit.Azure.ServiceBus.Core`. El dominio solo necesita `MassTransit.Abstractions` (interfaz `SagaStateMachineInstance`).

## Forma de la saga

- Instancia: clase con `CorrelationId`, `CurrentState` (string) y los datos del proceso; la lógica de dominio (generar un código, aceptar o no) en métodos de la instancia, no en la máquina.
- Máquina: `MassTransitStateMachine<TInstance>`; `InstanceState(x => x.CurrentState)`; `Event(() => X, x => x.CorrelateById(m => m.Message.Id))`; `Initially(When(...))`, `During(Estado, When(...), Ignore(...))`; `Finalize()` y `SetCompletedWhenFinalized()` para borrar la instancia al terminar. El resultado del proceso vive en el dominio o en los eventos publicados, no en estados terminales permanentes.
- La saga **solo publica mensajes**. No inyectar repositorios ni servicios en ella: lo que haya que hacer (activar un usuario, enviar un correo) lo hace un consumidor que recibe el evento.
- Plazos: `Schedule(() => Expiration, x => x.TokenId, x => { x.Delay = ...; x.Received = r => r.CorrelateById(...); })`, `.Schedule(Expiration, ...)` al empezar y `.Unschedule(Expiration)` al completar. Hace falta un scheduler: `AddSqlMessageScheduler`/`UseSqlMessageScheduler` (SQL), `AddDelayedMessageScheduler`/`UseDelayedMessageScheduler` (RabbitMQ con el plugin `rabbitmq_delayed_message_exchange`; la imagen `masstransit/rabbitmq` lo trae), `AddServiceBusMessageScheduler`/`UseServiceBusMessageScheduler` (Service Bus, nativo).

## Trampas

- Un evento no esperado en el estado actual lanza `UnhandledEventException` y manda el mensaje a la cola de error. Si es legítimo ignorarlo (un código incorrecto), `Ignore(Evento, filtro)` explícito.
- Un mensaje para una instancia que ya terminó va a la cola de error salvo `OnMissingInstance(m => m.Discard())` en la definición del evento.
- La saga publica dentro del comportamiento, **antes** de persistir la instancia; una respuesta inmediata puede no encontrarla. En producción, outbox transaccional de MassTransit; en tests, esperar a `Exists(id, estado)` antes de responder.
- Transporte SQL con autenticación integrada: el migrador siempre hace `CREATE LOGIN … WITH PASSWORD` y falla sin `Username`. Crear la base con EF antes de arrancar y poner `CreateDatabase = false` en `AddSqlServerMigrationHostedService`.
- Azure Service Bus: namespace Standard o Premium (Basic no tiene topics) y cadena **de namespace** con permiso Manage, nunca la de una cola (`EntityPath=` en la cadena da "does not match the EntityPath").
- Todos los servicios que comparten colas deben coincidir en transporte y, con SQL, en `Schema` y `Role`. Centralizar la configuración en un proyecto compartido (`AddMessaging`), no repetirla en cada `Program.cs`.

## Probarla

`AddMassTransitTestHarness` con el transporte en memoria; `harness.GetSagaStateMachineHarness<TMachine, TInstance>()` para `Exists(id, estado)`, `NotExists(id)` y `Sagas.Contains(id)`. Trampas: `Published.Select<T>()` **bloquea** hasta el timeout de inactividad; `Published.Any<T>()` devuelve `false` al agotarlo (subir `TestHarnessOptions.TestInactivityTimeout` si el test espera un plazo); los eventos ignorados con `Ignore` no aparecen en el `Consumed` del harness de la saga, sí en el del bus. Plazos de segundos en tests, inyectados por opciones.
