"""MySQL / MariaDB / Percona Server via PyMySQL, one session per run."""
import ssl
OS_NAME='MySQL'
VERSION_SQL='SELECT VERSION(), @@version_comment'

def format_product_identity(product_version, version_comment):
    """Use server-reported vendor/comment; do not manufacture enterprise editions."""
    import re
    number=str(product_version or '').strip()
    comment=' '.join(str(version_comment or '').split())
    both=(number+' '+comment).lower()
    if 'mariadb' in both:
        label='MariaDB Server'
        # version() usually contains -MariaDB; it is part of the actual version.
        detail=comment if comment and comment.lower() not in ('mariadb server','mariadb') and 'mariadb' not in comment.lower() else ''
    elif 'percona' in both:
        label='Percona Server'
        detail='(GPL)' if '(GPL)' in comment.upper() else ''
    else:
        label='MySQL'
        detail=comment
        if detail.lower().startswith('mysql'):
            detail=detail[5:].strip(' -')
    result=f'{label} {number}'.strip()
    if detail:
        result+=(' '+detail if detail.startswith('(') else ' ('+detail+')')
    return result[:128]

def get_version_info(conn,cursor):
    cursor.execute(VERSION_SQL)
    row=cursor.fetchone()
    return format_product_identity(row[0],row[1] if row and len(row)>1 else '') if row else ''


def connect(cfg):
    try:import pymysql
    except ImportError as e:raise RuntimeError('Install pymysql on Pandora Discovery server') from e
    mode=cfg.get('sslmode','required').strip()
    kwargs={}
    if mode not in ('disabled','required','verify-full'):
        raise ValueError('Invalid MySQL TLS mode')
    # PyMySQL supports TLS via an SSLContext. TLS is mandatory unless explicitly disabled.
    if mode!='disabled':
        if mode=='verify-full':
            context=ssl.create_default_context(cafile=cfg.get('ssl_ca') or None)
        else:
            context=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname=False
            context.verify_mode=ssl.CERT_NONE
        kwargs['ssl']=context
    port=int(cfg.get('port') or 3306)
    if not 1<=port<=65535:raise ValueError('Invalid MySQL port')
    return pymysql.connect(host=cfg['host'],port=port,user=cfg['user'],password=cfg.get('password',''),
            database=cfg.get('database') or 'mysql',connect_timeout=max(1,int(cfg.get('connect_timeout') or 10)),
            read_timeout=max(1,int(int(cfg.get('statement_timeout_ms') or 15000)/1000)),
            write_timeout=max(1,int(int(cfg.get('statement_timeout_ms') or 15000)/1000)),
            charset='utf8mb4',autocommit=True,program_name='PandoraFMS-MySQL-Discovery',**kwargs)

def init_session(conn,cursor,cfg):
    timeout=int(cfg.get('statement_timeout_ms') or 15000)
    # max_execution_time exists in MySQL/Percona, but not all MariaDB versions.
    # Dynamic values are integers controlled by the Discovery form.
    for sql in [f'SET SESSION MAX_EXECUTION_TIME = {timeout}',
                f'SET SESSION max_statement_time = {timeout/1000.0}']:
        try:cursor.execute(sql);break
        except Exception:pass
    try:cursor.execute('SET SESSION TRANSACTION READ ONLY')
    except Exception:pass

def before_query(conn,cursor,cfg):pass

def on_query_error(conn,cursor,cfg):pass
