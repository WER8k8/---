const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const { getPlatforms, getPlatformAccounts, createPlatformAccount, updatePlatformAccount, deletePlatformAccount } = require('../controllers/platform.controller');

router.get('/', authMiddleware, getPlatforms);
router.get('/:id/accounts', authMiddleware, getPlatformAccounts);
router.post('/:id/accounts', authMiddleware, createPlatformAccount);
router.put('/:id/accounts/:accountId', authMiddleware, updatePlatformAccount);
router.delete('/:id/accounts/:accountId', authMiddleware, deletePlatformAccount);

module.exports = router;
