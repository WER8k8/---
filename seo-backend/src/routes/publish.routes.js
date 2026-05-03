const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const { createPublishTask, getPublishTasks, getPublishTaskById, retryPublishTask, getPublishLogs } = require('../controllers/publish.controller');

router.post('/', authMiddleware, createPublishTask);
router.get('/', authMiddleware, getPublishTasks);
router.get('/logs', authMiddleware, getPublishLogs);
router.get('/:id', authMiddleware, getPublishTaskById);
router.post('/:id/retry', authMiddleware, retryPublishTask);

module.exports = router;
