const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const regionController = require('../controllers/region.controller');

router.get('/tree', authMiddleware, regionController.getRegionsTree);
router.get('/', authMiddleware, regionController.getRegionsList);
router.put('/batch-status', authMiddleware, regionController.batchUpdateStatus);

module.exports = router;
