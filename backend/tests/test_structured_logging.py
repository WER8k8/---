import unittest
import json
import logging
from io import StringIO
from app.core.log_context import set_log_context, get_log_context, clear_log_context
from app.core.logging_config import StructuredJsonFormatter, ContextEnrichFilter, LogConfig

class TestStructuredLogging(unittest.TestCase):
    def setUp(self):
        clear_log_context()
        
    def test_json_formatter_output(self):
        formatter = StructuredJsonFormatter()
        record = logging.LogRecord("test_logger", logging.INFO, "test_file.py", 10, "test message", None, None)
        record.tenant_id = "tenant-1"
        record.user_id = "user-1"
        record.trace_id = "trace-1"
        record.request_path = "/api/v1/test"
        
        output = formatter.format(record)
        data = json.loads(output)
        
        self.assertEqual(data["level"], "INFO")
        self.assertEqual(data["logger"], "test_logger")
        self.assertEqual(data["message"], "test message")
        self.assertEqual(data["tenant_id"], "tenant-1")
        self.assertEqual(data["user_id"], "user-1")
        self.assertEqual(data["trace_id"], "trace-1")
        self.assertEqual(data["request_path"], "/api/v1/test")
        self.assertIn("timestamp", data)
        self.assertIn("environment", data)
        
    def test_context_variables_in_log(self):
        set_log_context(tenant_id="tenant-x", user_id="user-y", trace_id="trace-z", request_path="/api/x")
        
        logger = logging.getLogger("test_context")
        logger.setLevel(logging.INFO)
        
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredJsonFormatter())
        handler.addFilter(ContextEnrichFilter())
        
        logger.addHandler(handler)
        logger.info("context message")
        logger.removeHandler(handler)
        
        output = stream.getvalue()
        data = json.loads(output)
        
        self.assertEqual(data["tenant_id"], "tenant-x")
        self.assertEqual(data["user_id"], "user-y")
        self.assertEqual(data["trace_id"], "trace-z")
        self.assertEqual(data["request_path"], "/api/x")
        self.assertEqual(data["message"], "context message")
        
    def test_context_clear(self):
        set_log_context(tenant_id="tenant-1")
        self.assertEqual(get_log_context()["tenant_id"], "tenant-1")
        
        clear_log_context()
        self.assertIsNone(get_log_context()["tenant_id"])
        self.assertIsNone(get_log_context()["user_id"])
        self.assertIsNone(get_log_context()["trace_id"])
        self.assertIsNone(get_log_context()["request_path"])
        
    def test_console_format_remains_readable(self):
        root, audit, perf = LogConfig.setup_logging(log_level="INFO")
        
        console_handler = next(h for h in root.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler))
        formatter = console_handler.formatter
        
        self.assertIsInstance(formatter, logging.Formatter)
        self.assertFalse(isinstance(formatter, StructuredJsonFormatter))
        
        self.assertIn("%(trace_id)s", formatter._fmt)

if __name__ == "__main__":
    unittest.main()
