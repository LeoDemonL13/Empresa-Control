import logging
from logging.config import fileConfig

from flask import current_app

from alembic import context

                                                   
                                                   
config = context.config

                                               
                                      
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')


def get_engine():
    try:
                                                           
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError):
                                             
        return current_app.extensions['migrate'].db.engine


def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace(
            '%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')


                                       
                            
                           
                                         
config.set_main_option('sqlalchemy.url', get_engine_url())
target_db = current_app.extensions['migrate'].db

                                                               
                  
                                                                     
          


def get_metadata():
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    return target_db.metadata


def _ajustar_timeouts(connection):
                                                                             

                                                                                
                                                                
                                                                                
                                                                        

                                                                               
                                                                              
                                                                                
                                                                              
                                                

                                                                            
                                                                        
                                                                           
                                                                               

                                                                            
       
    if connection.dialect.name != 'postgresql':
        return

    from sqlalchemy import text

    connection.execute(text('SET statement_timeout = 0'))
    connection.execute(text("SET lock_timeout = '5s'"))

    efectivo = connection.execute(text('SHOW statement_timeout')).scalar()
    bloqueo = connection.execute(text('SHOW lock_timeout')).scalar()
    logger.info(
        'Migraciones con statement_timeout=%s y lock_timeout=%s',
        'sin límite' if efectivo in ('0', None) else efectivo, bloqueo,
    )

                                                                              
                                                                               
                                                                             
                                                                                
                                                                                
                                                                               
                                                                       
     
                                                                               
                                                                                
                                                                      
    connection.commit()


def run_migrations_offline():
                                        

                                               
                                                     
                                                  
                                               

                                                                
                  

       
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=get_metadata(), literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
                                       

                                                
                                                

       

                                                                             
                                             
                                                                        
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    conf_args = current_app.extensions['migrate'].configure_args
    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives

    connectable = get_engine()

    with connectable.connect() as connection:
        _ajustar_timeouts(connection)

        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            **conf_args
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
