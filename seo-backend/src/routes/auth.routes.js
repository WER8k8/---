const express = require('express');
const router = express.Router();
const authController = require('../controllers/auth.controller');
const authUnifiedGate = require('../controllers/authUnifiedGate.controller');
const authMiddleware = require('../middleware/auth');

router.all('/login', authUnifiedGate.handleAuthLogin);
router.post('/refresh', authController.refreshToken);
router.get('/profile', authMiddleware, authController.getProfile);
router.put('/password', authMiddleware, authController.updatePassword);

module.exports = router;
