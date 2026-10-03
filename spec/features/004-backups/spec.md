# 004 · Backups de Base de Datos

**Estado:** implementado ✅

## Qué hace

Provee un mecanismo simple y directo para generar y descargar un snapshot íntegro de la base SQLite del sistema, sin depender de librerías externas ni de una infraestructura cloud[cite: 2].

## Por qué

Al ser un sistema diseñado como aplicación local en Windows sin infraestructura cloud inicial, el resguardo de los datos recae completamente en el usuario. Se requiere una herramienta que evite la pérdida del historial y del catálogo ante fallos del hardware o corrupción no intencional[cite: 2].

## Criterios de aceptación

- [x] Un botón accesible desde la interfaz web permite al usuario gatillar la descarga del backup.[cite: 2].
- [x] La copia generada representa el estado exacto de los datos hasta el instante de la descarga, mediante un snapshot de SQLite.[cite: 2].
- [x] El archivo descargado es un SQLite válido con integridad verificada.

## Fuera de alcance

- Respaldos automatizados en servicios en la nube (ej. Google Drive o AWS S3) para mantener la arquitectura inicial simple[cite: 2].
- Restauración de copias de seguridad de forma visual desde el propio dashboard[cite: 2].