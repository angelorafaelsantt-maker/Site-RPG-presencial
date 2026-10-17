import os,sqlite3,secrets,hashlib,hmac,json,threading
from flask import Flask,request,jsonify,send_from_directory,session
from werkzeug.security import generate_password_hash,check_password_hash
app=Flask(__name__,static_folder='static');app.secret_key=os.environ.get('SECRET_KEY',secrets.token_hex(32));app.config.update(SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=os.environ.get('HTTPS','0')=='1')
DB=os.environ.get('DB_PATH','rpg.sqlite3');lock=threading.RLock()
def db():
 c=sqlite3.connect(DB,timeout=15);c.row_factory=sqlite3.Row;c.execute('PRAGMA busy_timeout=15000');return c
with db() as c:
 c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL DEFAULT "player")')
 c.execute('CREATE TABLE IF NOT EXISTS characters (id INTEGER PRIMARY KEY, name TEXT NOT NULL, personality TEXT NOT NULL DEFAULT "", history TEXT NOT NULL DEFAULT "", relations TEXT NOT NULL DEFAULT "", items TEXT NOT NULL DEFAULT "", image TEXT NOT NULL DEFAULT "", owner_id INTEGER UNIQUE REFERENCES users(id))')
 if not c.execute('SELECT 1 FROM characters').fetchone():
  c.execute('INSERT INTO characters(name,personality,history,relations,items) VALUES (?,?,?,?,?)',('A Guardiã','Reservada, corajosa e leal.','Criada entre muralhas antigas.','Um mentor desaparecido.','Medalhão e espada.'))
  c.execute('INSERT INTO characters(name,personality,history,relations,items) VALUES (?,?,?,?,?)',('O Errante','Curioso e espirituoso.','Uma chave mudou seu destino.','Uma irmã distante.','Um mapa.'))
def current():
 with db() as c:return c.execute('SELECT id,username,role FROM users WHERE id=?',(session.get('uid',-1),)).fetchone()
def output(c,master=False,uid=None):
 d=dict(c);d['reserved']=d['owner_id'] is not None;d['mine']=d['owner_id']==uid
 if not master:
  d.pop('owner_id',None)
  if not d['mine'] :
   for key in ['history','relations','items']:d.pop(key,None)
 return d
@app.get('/')
def home():return send_from_directory('static','index.html')
@app.get('/api/me')
def me():
 u=current();return jsonify(dict(u) if u else None)
@app.post('/api/register')
def register():
 a=request.get_json(silent=True) or {};name=str(a.get('username','')).strip();pw=str(a.get('password',''))
 if not (3<=len(name)<=32 and len(pw)>=8):return jsonify(error='Usuário de 3 a 32 caracteres e senha com ao menos 8.'),400
 try:
  with db() as c:
   cur=c.execute('INSERT INTO users(username,password,role) VALUES (?, ?, "player")',(name,generate_password_hash(pw)))
   session['uid']=cur.lastrowid
 except sqlite3.IntegrityError:return jsonify(error='Esse nome de usuário já existe.'),409
 return jsonify(ok=True)
@app.post('/api/login')
def login():
 a=request.get_json(silent=True) or {}
 with db() as c:u=c.execute('SELECT * FROM users WHERE username=?',(str(a.get('username','')).strip(),)).fetchone()
 if not u or not check_password_hash(u['password'],str(a.get('password',''))):return jsonify(error='Credenciais inválidas.'),401
 session['uid']=u['id'];return jsonify(ok=True,role=u['role'])
@app.post('/api/logout')
def logout():session.clear();return jsonify(ok=True)
@app.get('/api/characters')
def characters():
 u=current()
 if not u:return jsonify(error='Faça login.'),401
 with db() as c:
  rows=c.execute('SELECT characters.*,users.username AS owner_name FROM characters LEFT JOIN users ON users.id=characters.owner_id ORDER BY characters.id').fetchall()
 return jsonify([output(r,u['role']=='master',u['id']) for r in rows])
@app.post('/api/choose/<int:cid>')
def choose(cid):
 u=current()
 if not u or u['role']!='player':return jsonify(error='Entre como jogador.'),403
 with lock:
  with db() as c:
   c.execute('BEGIN IMMEDIATE')
   if c.execute('SELECT 1 FROM characters WHERE owner_id=?',(u['id'],)).fetchone():return jsonify(error='Você já escolheu um personagem.'),409
   cur=c.execute('UPDATE characters SET owner_id=? WHERE id=? AND owner_id IS NULL',(u['id'],cid))
   if cur.rowcount!=1:return jsonify(error='Esse personagem já foi escolhido.'),409
 return jsonify(ok=True)
@app.post('/api/admin/characters')
def add():
 u=current()
 if not u or u['role']!='master':return jsonify(error='Apenas mestre.'),403
 a=request.get_json(silent=True) or {}
 with db() as c:
  cur=c.execute('INSERT INTO characters(name,personality,history,relations,items,image) VALUES (?,?,?,?,?,?)',tuple(str(a.get(k,''))[:1500000] for k in ['name','personality','history','relations','items','image']))
 return jsonify(id=cur.lastrowid)
@app.put('/api/admin/characters/<int:cid>')
def edit(cid):
 u=current()
 if not u or u['role']!='master':return jsonify(error='Apenas mestre.'),403
 a=request.get_json(silent=True) or {};keys=['name','personality','history','relations','items','image']
 with db() as c:c.execute('UPDATE characters SET '+','.join(k+'=?' for k in keys)+' WHERE id=?',tuple(str(a.get(k,''))[:1500000] for k in keys)+(cid,))
 return jsonify(ok=True)
@app.delete('/api/admin/characters/<int:cid>')
def delete(cid):
 u=current()
 if not u or u['role']!='master':return jsonify(error='Apenas mestre.'),403
 with db() as c:c.execute('DELETE FROM characters WHERE id=?',(cid,))
 return jsonify(ok=True)
@app.post('/api/admin/release/<int:cid>')
def release(cid):
 u=current()
 if not u or u['role']!='master':return jsonify(error='Apenas mestre.'),403
 with db() as c:c.execute('UPDATE characters SET owner_id=NULL WHERE id=?',(cid,))
 return jsonify(ok=True)
@app.post('/api/setup-master')
def setup_master():
 a=request.get_json(silent=True) or {};token=os.environ.get('MASTER_SETUP_TOKEN','')
 if not token:return jsonify(error='Configure MASTER_SETUP_TOKEN no servidor.'),503
 if not hmac.compare_digest(str(a.get('token','')),token):return jsonify(error='Código inválido.'),403
 name=str(a.get('username','')).strip();pw=str(a.get('password',''))
 if len(name)<3 or len(pw)<8:return jsonify(error='Nome e senha inválidos.'),400
 with lock:
  with db() as c:
   c.execute('BEGIN IMMEDIATE')
   if c.execute("SELECT 1 FROM users WHERE role='master'").fetchone():return jsonify(error='O mestre já foi criado.'),409
   try:cur=c.execute('INSERT INTO users(username,password,role) VALUES (?, ?, "master")',(name,generate_password_hash(pw)))
   except sqlite3.IntegrityError:return jsonify(error='Nome já utilizado.'),409
   session['uid']=cur.lastrowid
 return jsonify(ok=True)
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
