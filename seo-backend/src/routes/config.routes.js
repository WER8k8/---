const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const { getConfigs, getConfigByGroup, updateConfig } = require('../controllers/config.controller');

router.get('/', authMiddleware, getConfigs);
router.get('/:group', authMiddleware, getConfigByGroup);
router.put('/:group', authMiddleware, updateConfig);

module.exports = router;
