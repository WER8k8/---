const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const { getIndexingRecords, checkIndex, getAlerts, handleAlert } = require('../controllers/monitoring.controller');

router.get('/indexing', authMiddleware, getIndexingRecords);
router.post('/indexing/check', authMiddleware, checkIndex);
router.get('/alerts', authMiddleware, getAlerts);
router.post('/alerts/:id/handle', authMiddleware, handleAlert);

module.exports = router;
