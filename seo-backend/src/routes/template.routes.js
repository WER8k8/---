const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const { getTemplates, getTemplateById, createTemplate, updateTemplate, deleteTemplate } = require('../controllers/template.controller');

router.get('/', authMiddleware, getTemplates);
router.get('/:id', authMiddleware, getTemplateById);
router.post('/', authMiddleware, createTemplate);
router.put('/:id', authMiddleware, updateTemplate);
router.delete('/:id', authMiddleware, deleteTemplate);

module.exports = router;
