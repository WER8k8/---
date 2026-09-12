const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const { getOperationLogs, getLoginLogs } = require('../controllers/log.controller');

router.get('/operations', authMiddleware, getOperationLogs);
router.get('/logins', authMiddleware, getLoginLogs);

module.exports = router;
