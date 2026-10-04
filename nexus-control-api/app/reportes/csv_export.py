import csv
import io


def generar_csv(columnas: list, filas: list) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(columnas)
    writer.writerows(filas)
    return buffer.getvalue().encode('utf-8-sig')
