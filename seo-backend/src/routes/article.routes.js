const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const { getArticles, getArticleById, createArticle, updateArticle, deleteArticle, generateArticles, getArticleStats } = require('../controllers/article.controller');

router.get('/', authMiddleware, getArticles);
router.get('/stats', authMiddleware, getArticleStats);
router.get('/:id', authMiddleware, getArticleById);
router.post('/', authMiddleware, createArticle);
router.post('/generate', authMiddleware, generateArticles);
router.put('/:id', authMiddleware, updateArticle);
router.delete('/:id', authMiddleware, deleteArticle);

module.exports = router;
