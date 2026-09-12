/**
 * sqlite3-shim: Wraps better-sqlite3 to provide a compatible API for Sequelize.
 * Sequelize expects the sqlite3 package which has a Database class.
 * better-sqlite3 has a different API, so we create a shim.
 * 
 * Key Sequelize usage:
 * - new Database(filename, mode, callback)
 * - connection.run(sql, params, callback) - callback called with (err), this = {lastID, changes}
 * - connection.get(sql, params, callback) - callback called with (err, row)
 * - connection.all(sql, params, callback) - callback called with (err, rows)
 * - connection.exec(sql, callback) - callback called with (err)
 * - connection.close(callback) - callback called with (err)
 * - connection.serialize(callback)
 * - connection.parallelize(callback)
 */
const BetterSqlite3 = require('better-sqlite3');

module.exports = {
  OPEN_READONLY: 1,
  OPEN_READWRITE: 2,
  OPEN_CREATE: 4,
  
  Database: class SQLite3Database {
    constructor(filename, mode, callback) {
      // Handle optional mode parameter
      if (typeof mode === 'function') {
        callback = mode;
        mode = undefined;
      }
      try {
        this.db = new BetterSqlite3(filename);
        // Defer callback to next tick so outer variable is assigned
        if (callback) process.nextTick(() => callback(null));
      } catch (err) {
        if (callback) process.nextTick(() => callback(err));
      }
    }
    
    run(sql, params, callback) {
      // Handle case where params is the callback
      if (typeof params === 'function') {
        callback = params;
        params = [];
      }
      // Convert $1, $2, ... placeholders to @p1, @p2, ... for better-sqlite3
      const convertedSql = sql.replace(/\$(\d+)/g, '@p$1');
      try {
        const stmt = this.db.prepare(convertedSql);
        let info;
        if (Array.isArray(params) && params.length > 0) {
          // Convert array params to object with named params (better-sqlite3 compat)
          // Sequelize uses $1, $2, ... format; better-sqlite3 expects keys without $
          const paramObj = {};
          params.forEach((v, i) => { paramObj[`p${i+1}`] = v; });
          info = stmt.run(paramObj);
        } else if (params && typeof params === 'object' && !Array.isArray(params)) {
          // Convert $1, $2 keys to p1, p2 for better-sqlite3 compatibility
          const paramObj = {};
          for (const [k, v] of Object.entries(params)) {
            // $1 -> p1, $2 -> p2, @p1 -> p1, :p1 -> p1
            const cleanKey = k.replace(/^[\$:@]/, '');
            paramObj[cleanKey.match(/^\d+$/) ? `p${cleanKey}` : cleanKey] = v;
          }
          info = stmt.run(paramObj);
        } else {
          info = stmt.run();
        }
        // Call callback with `this` context having lastID and changes (sqlite3 compat)
        if (callback) {
          const ctx = { lastID: info.lastInsertRowid, changes: info.changes };
          callback.call(ctx, null);
        }
      } catch (err) {
        if (callback) callback(err);
      }
    }
    
    get(sql, params, callback) {
      if (typeof params === 'function') {
        callback = params;
        params = [];
      }
      const convertedSql = sql.replace(/\$(\d+)/g, '@p$1');
      try {
        const stmt = this.db.prepare(convertedSql);
        let row;
        if (Array.isArray(params) && params.length > 0) {
          const paramObj = {};
          params.forEach((v, i) => { paramObj[`p${i+1}`] = v; });
          row = stmt.get(paramObj);
        } else if (params && typeof params === 'object' && !Array.isArray(params)) {
          const paramObj = {};
          for (const [k, v] of Object.entries(params)) {
            const cleanKey = k.replace(/^[\$:@]/, '');
            paramObj[cleanKey.match(/^\d+$/) ? `p${cleanKey}` : cleanKey] = v;
          }
          row = stmt.get(paramObj);
        } else {
          row = stmt.get();
        }
        if (callback) callback(null, row);
      } catch (err) {
        if (callback) callback(err);
      }
    }
    
    all(sql, params, callback) {
      if (typeof params === 'function') {
        callback = params;
        params = [];
      }
      const convertedSql = sql.replace(/\$(\d+)/g, '@p$1');
      try {
        const stmt = this.db.prepare(convertedSql);
        let rows;
        try {
          if (Array.isArray(params) && params.length > 0) {
            const paramObj = {};
            params.forEach((v, i) => { paramObj[`p${i+1}`] = v; });
            rows = stmt.all(paramObj);
          } else if (params && typeof params === 'object' && !Array.isArray(params)) {
            const paramObj = {};
            for (const [k, v] of Object.entries(params)) {
              const cleanKey = k.replace(/^[\$:@]/, '');
              paramObj[cleanKey.match(/^\d+$/) ? `p${cleanKey}` : cleanKey] = v;
            }
            rows = stmt.all(paramObj);
          } else {
            rows = stmt.all();
          }
        } catch (stmtErr) {
          // If all() fails (e.g. for non-SELECT), fall back to run
          if (stmtErr.message.includes('This statement does not return data')) {
            if (Array.isArray(params) && params.length > 0) {
              const paramObj = {};
              params.forEach((v, i) => { paramObj[`p${i+1}`] = v; });
              stmt.run(paramObj);
            } else if (params && typeof params === 'object' && !Array.isArray(params)) {
              const paramObj = {};
              for (const [k, v] of Object.entries(params)) {
                const cleanKey = k.replace(/^[\$:@]/, '');
                paramObj[cleanKey.match(/^\d+$/) ? `p${cleanKey}` : cleanKey] = v;
              }
              stmt.run(paramObj);
            } else {
              stmt.run();
            }
            rows = [];
          } else {
            throw stmtErr;
          }
        }
        if (callback) callback(null, rows);
      } catch (err) {
        if (callback) callback(err);
      }
    }
    
    exec(sql, callback) {
      try {
        this.db.exec(sql);
        if (callback) callback(null);
      } catch (err) {
        if (callback) callback(err);
      }
    }
    
    close(callback) {
      try {
        this.db.close();
        if (callback) callback(null);
      } catch (err) {
        if (callback) callback(err);
      }
    }
    
    serialize(callback) {
      // better-sqlite3 is synchronous, so just call callback
      if (callback) callback(null);
    }
    
    parallelize(callback) {
      if (callback) callback(null);
    }
  },
  
  verbose: () => module.exports,
};
