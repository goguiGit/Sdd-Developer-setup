---
pbi: 1234
title: Límite de intentos de confirmación
feature: registro-usuario
status: approved
---
## Por qué

Un código de seis dígitos con 24 horas de plazo admite un ataque por fuerza bruta: un millón de combinaciones caben de sobra en ese tiempo. Hoy un código incorrecto no tiene ninguna consecuencia (REQ-REG-003).

## ADDED

### REQ-REG-006 Límite de intentos fallidos
GIVEN un usuario pendiente que ya ha enviado cuatro códigos incorrectos
WHEN envía un quinto código incorrecto
THEN el registro se descarta igual que al caducar y se avisa a la persona de que debe registrarse de nuevo

## MODIFIED

### REQ-REG-003 Código incorrecto
GIVEN un usuario pendiente dentro del plazo con menos de cuatro intentos fallidos
WHEN confirma con un código distinto al que recibió
THEN el usuario sigue pendiente, se cuenta el intento y puede volver a intentarlo

## REMOVED

## Plan

- [ ] Test: el quinto código incorrecto publica `RegistrationDiscarded` (saga, `RegistrationStateMachineTests`)
- [ ] Test: el cuarto código incorrecto deja la saga en `AwaitingConfirmation` con `FailedAttempts = 4`
- [ ] `RegistrationState.FailedAttempts` y `RegistrationState.Reject()` en el dominio
- [ ] Rama `Ignore` de `EmailConfirmed` pasa a `When` que incrementa y decide
- [ ] README de la demo: sección de seguridad del código
