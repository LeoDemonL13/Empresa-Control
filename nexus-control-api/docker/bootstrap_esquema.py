                                                                          

                  
                  
                                                                             
                                                                             
                                                                               
                                                                           
                                                                           
                                                                           
                  

        
        
                                                                           
                                                                     
                                               

       
       
                                                                         
                                                                          
                                                                        

                                                                             
                                                                 
   

import os
import sys

                                                                            
                                                                      
                                                                  
sys.path.insert(0, os.getcwd())


def _tablas_existentes() -> set:
                                                    

                                                                           
                                                                           
                                                                             
                                                                            
       
    from sqlalchemy import create_engine, inspect
    from sqlalchemy.pool import NullPool

    url = os.environ.get('DATABASE_URL', '')
    if not url:
        return set()
    motor = create_engine(url, poolclass=NullPool)
    try:
        return set(inspect(motor).get_table_names())
    finally:
        motor.dispose()


def main() -> int:
    tablas = _tablas_existentes()

    if 'alembic_version' in tablas:
        print('[bootstrap] La base ya está bajo control de Alembic. Nada que hacer.')
        return 0

    if tablas:
        print(
            '[bootstrap] La base tiene tablas pero no `alembic_version`.\n'
            f'            Tablas encontradas: {len(tablas)}.\n'
            '            NO se toca nada: revisa a mano si hace falta un '
            '`flask db stamp <revisión>`.',
            file=sys.stderr,
        )
        return 1

    print('[bootstrap] Base vacía: creando el esquema desde los modelos...')

    from app import create_app
    from app.extensions import db

    app = create_app()
    with app.app_context():
        db.create_all()

        from flask_migrate import stamp
        stamp(revision='head')

    print('[bootstrap] Esquema creado y marcado en la última revisión.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
