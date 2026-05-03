const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const { getDashboardStats, getTrendData } = require('../controllers/dashboard.controller');

router.get('/stats', authMiddleware, getDashboardStats);
router.get('/trend', authMiddleware, getTrendData);

module.exports = router;
