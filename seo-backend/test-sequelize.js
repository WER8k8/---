const { Sequelize, DataTypes } = require('sequelize');
const s = new Sequelize({ dialect: 'sqlite', storage: ':memory:', dialectModule: require('./src/config/sqlite3-shim') });
const User = s.define('User', { name: DataTypes.STRING });

s.sync().then(() => {
  console.log('Sync OK');
  return User.create({ name: 'test' });
}).then(u => {
  console.log('Created:', u.toJSON());
  return User.findAll();
}).then(users => {
  console.log('Found:', users.length, 'users');
  process.exit(0);
}).catch(e => {
  console.error('FAIL:', e.message);
  process.exit(1);
});
