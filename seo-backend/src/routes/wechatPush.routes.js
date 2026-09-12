const express = require('express');
const router = express.Router();
const wechatPushController = require('../controllers/wechatPush.controller');
const authMiddleware = require('../middleware/auth');

router.get('/config', authMiddleware, wechatPushController.getWechatPushConfig);
router.put('/config', authMiddleware, wechatPushController.updateWechatPushConfig);
router.get('/logs', authMiddleware, wechatPushController.getPushLogs);
router.post('/manual/send', authMiddleware, wechatPushController.manualSendDaily);

module.exports = router;
