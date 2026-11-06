import unittest
import httpx
from core.image_generation import image_limit_error

class ImageLimitTests(unittest.TestCase):
    def test_specific_billing_categories(self):
        for code, phrase in [('credit_balance_exhausted','prepaid credits'),('organization_spend_limit_exceeded','organization spending'),('project_spend_limit_exceeded','project spending'),('organization_usage_limit_exceeded','approved usage'),('insufficient_quota','insufficient quota')]:
            with self.subTest(code=code):
                error = image_limit_error(httpx.Response(429,json={'error':{'code':code,'type':'insufficient_quota','message':'secret-key'}}))
                self.assertIn(phrase,str(error))
                self.assertNotIn('secret-key',str(error))
                self.assertEqual(error.status_code,429)
    def test_rate_limit_honors_retry_delay(self):
        error=image_limit_error(httpx.Response(429,headers={'Retry-After':'75'},json={'error':{'code':'rate_limit_exceeded'}}))
        self.assertIn('75 seconds',str(error))
    def test_unrecognized_and_malformed_do_not_claim_temporary_failure(self):
        for body in [{'error':{'message':'secret-key','code':'unknown'}},{'error':[]},[],{'error':{'code':[]}}]:
            error=image_limit_error(httpx.Response(429,json=body))
            self.assertIn('did not identify',str(error))
            self.assertNotIn('secret-key',str(error))
    def test_legacy_quota_type(self):
        self.assertIn('insufficient quota',str(image_limit_error(httpx.Response(429,json={'error':{'type':'insufficient_quota'}}))))
