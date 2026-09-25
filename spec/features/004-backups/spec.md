# 004 · Backups de Base de Datos

**Estado:** en curso 🔜

## Qué hace

Provee un mecanismo simple y directo para generar y descargar una copia de seguridad exacta del archivo de la base de datos local[cite: 2].

## Por qué

Al ser un sistema diseñado como aplicación local en Windows sin infraestructura cloud inicial, el resguardo de los datos recae completamente en el usuario. Se requiere una herramienta que evite la pérdida del historial y del catálogo ante fallos del hardware[cite: 2].

## Criterios de aceptación

- [ ] Un botón accesible desde la interfaz web permite al usuario gatillar la descarga del archivo `db.sqlite3`[cite: 2].
- [ ] La copia generada representa el estado exacto de los datos hasta el instante de la descarga[cite: 2].

## Fuera de alcance

- Respaldos automatizados en servicios en la nube (ej. Google Drive o AWS S3) para mantener la arquitectura inicial simple[cite: 2].
- Restauración de copias de seguridad de forma visual desde el propio dashboard[cite: 2].