                                                                        

                                                                            
                                                                              
                                                                              
                  
   

import os
import sys


def main() -> int:
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        print('(sin DATABASE_URL)')
        return 0

    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import NullPool

    motor = create_engine(url, poolclass=NullPool)
    try:
        with motor.connect() as conexion:
            revision = conexion.execute(
                text('SELECT version_num FROM alembic_version')
            ).scalar()
        print(revision or '(sin revisión)')
        return 0
    except Exception as exc:                
                                                                              
                                             
        print(f'(no se pudo leer: {exc.__class__.__name__})')
        return 0
    finally:
        motor.dispose()


if __name__ == '__main__':
    sys.exit(main())
