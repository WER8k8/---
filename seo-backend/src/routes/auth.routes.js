const express = require('express');
const router = express.Router();
const authController = require('../controllers/auth.controller');
const authMiddleware = require('../middleware/auth');

router.post('/login', authController.login);
router.post('/refresh', authController.refreshToken);
router.get('/profile', authMiddleware, authController.getProfile);
router.put('/password', authMiddleware, authController.updatePassword);

module.exports = router;
