"""MySQL / MariaDB / Percona Server via PyMySQL, one session per run."""
import ssl
OS_NAME='MySQL'

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
