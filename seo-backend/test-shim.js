const shim = require('./src/config/sqlite3-shim');

const conn = new shim.Database(':memory:', (err) => {
  if (err) { console.error('DB open error:', err); process.exit(1); }
  
  conn.run('CREATE TABLE t(id INTEGER PRIMARY KEY, name TEXT)');
  
  // Test with $1 style params (Sequelize format)
  const sql = 'INSERT INTO t(name) VALUES($1)';
  console.log('Original SQL:', sql);
  
  conn.run(sql, ['test'], function(e) {
    console.log('run err:', e);
    console.log('this.lastID:', this.lastID, 'changes:', this.changes);
    
    conn.all('SELECT * FROM t', [], (err, rows) => {
      console.log('rows:', rows);
    });
  });
});
