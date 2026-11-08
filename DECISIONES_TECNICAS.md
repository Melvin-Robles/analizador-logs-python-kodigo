# Registro de decisiones técnicas


1. Una línea completamente válida contiene una severidad reconocida, una fecha válida YYYY-MM-DD y un mensaje no vacío.
2. Solo se reconocen INFO, WARNING y ERROR en mayúsculas y entre corchetes.
3. Las fechas se validan con expresión regular y con datetime; se distinguen fechas válidas, ausentes e inválidas.
4. Una severidad reconocida con mensaje, pero sin fecha, es una línea incompleta.
5. Un mensaje ausente produce una línea incompleta.
6. El total de eventos cuenta todas las líneas no vacías.
7. Las severidades reconocidas se cuentan aunque la línea tenga otros problemas.
8. Las severidades desconocidas se cuentan aparte y no se clasifican como ERROR.
9. Una línea con varios problemas solo suma una vez en incompletas o mal formadas.
10. Las líneas vacías se ignoran.
11. Se permiten espacios adicionales al inicio, final y entre componentes.
12. El mensaje puede contener espacios, números y caracteres adicionales.
13. Los archivos se leen como UTF-8.
14. Las rutas inexistentes o ilegibles generan una advertencia y permiten cancelar o volver a intentar.
15. La ruta se introduce en la consola


## Decisiones de diseño sugeridas por la IA y aprobadas por mi

- Separar extracción, validación, estadísticas, lectura de archivo y presentación.
- Usar dataclass para representar el resultado de una línea y las estadísticas.
- Mantener la lógica de análisis independiente de input() y print() para facilitar las pruebas.
- Crear un archivo correcto y otro inconsistente para validar casos normales y casos límite.
