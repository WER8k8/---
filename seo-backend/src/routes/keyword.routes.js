const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const { getKeywords, getKeywordById, createKeyword, updateKeyword, deleteKeyword, generateLongtailKeywords } = require('../controllers/keyword.controller');

router.get('/', authMiddleware, getKeywords);
router.get('/:id', authMiddleware, getKeywordById);
router.post('/', authMiddleware, createKeyword);
router.put('/:id', authMiddleware, updateKeyword);
router.delete('/:id', authMiddleware, deleteKeyword);
router.post('/generate', authMiddleware, generateLongtailKeywords);

module.exports = router;
