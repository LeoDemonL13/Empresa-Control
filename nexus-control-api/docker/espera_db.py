                                                                             

                                                                              
                                                                            
                                                                           
                                                                         
                                                                   

                                                                              
                                                                            
                                                                          
   

import os
import sys
import time

TIEMPO_MAXIMO = int(os.environ.get('DB_ESPERA_SEGUNDOS', '60'))
INTERVALO = 2


def main() -> int:
    url = os.environ.get('DATABASE_URL', '')

                                                                       
    if not url or url.startswith('sqlite'):
        return 0

    from sqlalchemy import create_engine, text

                                                                      
                                                         
    from sqlalchemy.pool import NullPool
    motor = create_engine(url, poolclass=NullPool)

    limite = time.monotonic() + TIEMPO_MAXIMO
    ultimo_error = None
    while time.monotonic() < limite:
        try:
            with motor.connect() as conexion:
                conexion.execute(text('SELECT 1'))
            print('[entrypoint] La base de datos responde.', flush=True)
            return 0
        except Exception as exc:                                                        
            ultimo_error = exc
            print('[entrypoint] Esperando a la base de datos...', flush=True)
            time.sleep(INTERVALO)

    print(
        f'[entrypoint] CRÍTICO: la base de datos no respondió en {TIEMPO_MAXIMO}s.\n'
        f'             Último error: {ultimo_error}',
        file=sys.stderr,
        flush=True,
    )
    return 1


if __name__ == '__main__':
    sys.exit(main())
