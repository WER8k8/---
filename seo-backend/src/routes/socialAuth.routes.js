const express = require('express');
const router = express.Router();
const socialAuthController = require('../controllers/socialAuth.controller');
const authMiddleware = require('../middleware/auth');

router.post('/email/code', socialAuthController.sendEmailCode);
router.post('/email/login', socialAuthController.emailLogin);
router.post('/qq/auth', socialAuthController.qqAuth);
router.post('/wechat/auth', socialAuthController.wechatAuth);
router.get('/bind/status', authMiddleware, socialAuthController.getBindStatus);

module.exports = router;
