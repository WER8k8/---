const logger = require('../utils/logger');

const errorHandler = (err, req, res, next) => {
  const statusCode = err.statusCode || err.status || 500;
  const message = err.message || '服务器内部错误';

  const errorResponse = {
    code: statusCode,
    message: message,
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack }),
  };

  if (statusCode >= 500) {
    logger.error('Server Error:', {
      path: req.path,
      method: req.method,
      error: err.message,
      stack: err.stack,
      body: req.body,
      query: req.query,
    });
  } else if (statusCode >= 400) {
    logger.warn('Client Error:', {
      path: req.path,
      method: req.method,
      error: err.message,
    });
  }

  if (err.name === 'ValidationError') {
    errorResponse.code = 400;
    errorResponse.message = '数据验证失败';
    errorResponse.details = err.details || [];
  }

  if (err.name === 'UnauthorizedError') {
    errorResponse.code = 401;
    errorResponse.message = '未授权访问';
  }

  if (err.code === 'ECONNREFUSED') {
    errorResponse.code = 503;
    errorResponse.message = '服务暂时不可用';
  }

  res.status(statusCode).json(errorResponse);
};

const asyncHandler = fn => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

module.exports = { errorHandler, asyncHandler };
