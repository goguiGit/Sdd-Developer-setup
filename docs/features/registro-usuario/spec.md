---
feature: registro-usuario
title: Registro de usuario con confirmación de email
---
# Registro de usuario con confirmación de email

Una persona se registra con su correo, recibe un código y tiene un plazo para confirmarlo. Si confirma, la cuenta se activa; si no, el registro se descarta. Ejemplo tomado de [MassTransit.Saga.Demo](https://github.com/goguiGit/MassTransit.Saga.Demo).

## Requisitos

### REQ-REG-001 Alta pendiente de confirmación
GIVEN un correo con formato válido que no está registrado
WHEN la persona se registra
THEN existe un usuario en estado pendiente y se le envía un código de verificación de seis dígitos
Publica: UserRegistered, SendVerificationEmail

### REQ-REG-002 Confirmación con el código correcto
GIVEN un usuario pendiente dentro del plazo
WHEN confirma con el código que recibió
THEN el usuario pasa a activo y recibe el correo de bienvenida
Publica: UserActivated, SendWelcomeEmail

### REQ-REG-003 Código incorrecto
GIVEN un usuario pendiente dentro del plazo
WHEN confirma con un código distinto al que recibió
THEN el usuario sigue pendiente y puede volver a intentarlo

### REQ-REG-004 Caducidad del registro
GIVEN un usuario pendiente
WHEN vence el plazo de confirmación sin confirmar
THEN el registro se descarta y un código enviado después ya no tiene efecto
Publica: RegistrationDiscarded

### REQ-REG-005 Correo inválido
GIVEN un texto que no es un correo
WHEN la persona intenta registrarse
THEN se rechaza con el motivo y no se crea ningún usuario

## Decisiones

- El plazo y el código los guarda y decide la saga, no la API: la API acepta cualquier código bien formado y la saga lo evalúa. Alternativa descartada: validar el código en la API; obligaría a compartir el secreto entre dos componentes.
- El usuario existe desde el registro, en estado pendiente, para que el estado sea consultable. Alternativa descartada: crearlo al confirmar.

## Historial

| Fecha | PBI | Cambio |
|---|---|---|
| 2026-10-30 | 1000 | Spec inicial |
